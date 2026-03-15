import asyncio
import json
from datetime import datetime
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.core.containers import Container
from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.job import JobCreate, JobHistory, JobRead, JobStatus
from app.services.job import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobRead, status_code=201)
@inject
async def create_job(
    payload: JobCreate,
    session: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
    service: JobService = Depends(Provide[Container.job_service]),
) -> JobRead:
    return await service.create_job(session, payload, user_id)


@router.get("", response_model=list[JobHistory])
@inject
async def list_jobs(
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
    service: JobService = Depends(Provide[Container.job_service]),
) -> list[JobHistory]:
    rows = await service.list_jobs(session, user_id, limit=limit, offset=offset)
    return [JobHistory(**row) for row in rows]


@router.delete("/{job_id}", status_code=204)
@inject
async def delete_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
    service: JobService = Depends(Provide[Container.job_service]),
) -> None:
    await service.delete_job(session, job_id, user_id)


@router.get("/{job_id}", response_model=JobStatus)
@inject
async def get_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
    service: JobService = Depends(Provide[Container.job_service]),
) -> JobStatus:
    return await service.get_status(session, job_id, user_id=user_id)


@router.get("/{job_id}/stream")
@inject
async def stream_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
    redis=Depends(Provide[Container.redis_client]),
    service: JobService = Depends(Provide[Container.job_service]),
) -> EventSourceResponse:
    async def event_generator():
        # Check if job already finished before subscribing (race condition guard)
        # Also enforces ownership — raises 403 if user_id doesn't match
        current = await service.get_status(session, job_id, user_id=user_id)
        if current.status == "failed":
            error_msg = (current.result or {}).get("error", "Job failed")
            yield {"data": json.dumps({"type": "error", "message": error_msg})}
            return
        if current.status == "completed":
            output = (current.result or {}).get("formatted_output", "")
            yield {"data": json.dumps({"type": "report", "node": "formatter", "data": {"title": "Report", "content": output}})}
            yield {"data": json.dumps({"type": "done", "job_id": str(job_id)})}
            return

        pubsub = redis.pubsub()
        await pubsub.subscribe(f"job:{job_id}")
        no_msg_ticks = 0
        try:
            while True:
                try:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True, timeout=5.0
                    )
                except Exception:
                    yield {"data": json.dumps({"type": "error", "message": "Stream connection lost. Please refresh the page."})}
                    break
                if message and message["type"] == "message":
                    no_msg_ticks = 0
                    data = message["data"]
                    yield {"data": data}
                    parsed = json.loads(data)
                    if parsed.get("type") in ("done", "error"):
                        break
                else:
                    no_msg_ticks += 1
                    # Every ~15s of silence — check DB for final status
                    if no_msg_ticks >= 3:
                        no_msg_ticks = 0
                        fallback = await service.get_status(session, job_id)
                        if fallback.status == "failed":
                            error_msg = (fallback.result or {}).get("error", "Job failed")
                            yield {"data": json.dumps({"type": "error", "message": error_msg})}
                            break
                        if fallback.status == "completed":
                            yield {"data": json.dumps({"type": "done", "job_id": str(job_id)})}
                            break
                        if fallback.status == "pending" and fallback.created_at:
                            age = (datetime.utcnow() - fallback.created_at).total_seconds()
                            if age > 30:
                                yield {"data": json.dumps({"type": "error", "message": "Worker is not responding. The queue may be overloaded — please try again."})}
                                break
                await asyncio.sleep(0.05)
        finally:
            await pubsub.unsubscribe(f"job:{job_id}")
            await pubsub.close()

    return EventSourceResponse(event_generator())
