from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.tool import Tool

STALE_PENDING_MINUTES = 5
STALE_RUNNING_MINUTES = 30


class JobRepository:
    async def create(
        self,
        session: AsyncSession,
        user_id: UUID,
        tool_id: UUID,
        input: dict,
    ) -> Job:
        job = Job(user_id=user_id, tool_id=tool_id, input=input)
        session.add(job)
        await session.flush()
        return job

    async def get_by_id(self, session: AsyncSession, job_id: UUID) -> Job | None:
        result = await session.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()

    async def _expire_stale_jobs(self, session: AsyncSession, user_id: UUID) -> None:
        now = datetime.utcnow()
        await session.execute(
            update(Job)
            .where(
                Job.user_id == user_id,
                Job.status == "pending",
                Job.created_at < now - timedelta(minutes=STALE_PENDING_MINUTES),
            )
            .values(status="failed", result={"error": "Job timed out in queue"}, completed_at=now)
        )
        await session.execute(
            update(Job)
            .where(
                Job.user_id == user_id,
                Job.status == "running",
                Job.created_at < now - timedelta(minutes=STALE_RUNNING_MINUTES),
            )
            .values(status="failed", result={"error": "Job timed out while running"}, completed_at=now)
        )

    async def get_by_user(
        self,
        session: AsyncSession,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        await self._expire_stale_jobs(session, user_id)

        result = await session.execute(
            select(Job, Tool.name.label("tool_name"), Tool.tool_type.label("tool_type"))
            .join(Tool, Job.tool_id == Tool.id)
            .where(Job.user_id == user_id)
            .order_by(desc(Job.created_at))
            .limit(limit)
            .offset(offset)
        )
        rows = result.all()
        return [
            {
                "id": row.Job.id,
                "tool_name": row.tool_name,
                "tool_type": row.tool_type,
                "tool_id": row.Job.tool_id,
                "status": row.Job.status,
                "query": row.Job.input.get("query", ""),
                "title": row.Job.title,
                "credits_used": row.Job.credits_used,
                "created_at": row.Job.created_at,
                "completed_at": row.Job.completed_at,
            }
            for row in rows
        ]

    async def delete(self, session: AsyncSession, job_id: UUID, user_id: UUID) -> bool:
        job = await self.get_by_id(session, job_id)
        if not job or job.user_id != user_id:
            return False
        await session.delete(job)
        return True

    async def set_running(self, session: AsyncSession, job_id: UUID) -> None:
        job = await self.get_by_id(session, job_id)
        if job:
            job.status = "running"

    async def set_completed(
        self, session: AsyncSession, job_id: UUID, result: dict, credits_used: int = 0
    ) -> None:
        job = await self.get_by_id(session, job_id)
        if job:
            job.status = "completed"
            job.result = result
            job.credits_used = credits_used
            job.completed_at = datetime.utcnow()

    async def set_failed(
        self, session: AsyncSession, job_id: UUID, error: str
    ) -> None:
        job = await self.get_by_id(session, job_id)
        if job:
            job.status = "failed"
            job.result = {"error": error}
            job.completed_at = datetime.utcnow()

    async def set_title(
        self, session: AsyncSession, job_id: UUID, title: str
    ) -> None:
        job = await self.get_by_id(session, job_id)
        if job:
            job.title = title
