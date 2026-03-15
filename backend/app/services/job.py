from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import FREEZE_CREDITS
from app.core.exceptions import NotFoundError
from app.models.tool import Tool
from app.repositories.job import JobRepository
from app.repositories.user import UserRepository
from app.schemas.job import JobCreate, JobRead, JobStatus
from app.tasks.code_review import run_code_review
from app.tasks.research import run_research_agent


class JobService:
    def __init__(
        self,
        repository: JobRepository,
        user_repository: UserRepository,
    ) -> None:
        self.repository = repository
        self.user_repository = user_repository

    async def create_job(
        self,
        session: AsyncSession,
        payload: JobCreate,
        user_id: UUID,
    ) -> JobRead:
        user = await self.user_repository.get_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        if user.credits_balance < 0:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient credits — top up your balance to run tools",
            )

        tool = await session.get(Tool, payload.tool_id)
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool not found",
            )

        try:
            await self.user_repository.deduct_credits(session, user_id, FREEZE_CREDITS)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            ) from e

        job = await self.repository.create(
            session,
            user_id=user_id,
            tool_id=payload.tool_id,
            input=payload.input,
        )
        await session.commit()

        if tool.tool_type == "research_agent":
            run_research_agent.delay(str(job.id), payload.input.get("query", ""), str(user_id))
        elif tool.tool_type == "code_review":
            run_code_review.delay(
                str(job.id),
                payload.input.get("code", ""),
                payload.input.get("language", ""),
                str(user_id),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tool type '{tool.tool_type}' is not yet supported",
            )

        return JobRead.model_validate(job)

    async def list_jobs(
        self,
        session: AsyncSession,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        return await self.repository.get_by_user(session, user_id, limit=limit, offset=offset)

    async def get_status(
        self,
        session: AsyncSession,
        job_id: UUID,
        user_id: UUID | None = None,
    ) -> JobStatus:
        job = await self.repository.get_by_id(session, job_id)
        if not job:
            raise NotFoundError("Job", job_id)
        if user_id is not None and job.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        
        # Get tool info
        tool = await session.get(Tool, job.tool_id)
        tool_type = tool.tool_type if tool else "unknown"
        
        return JobStatus(
            id=job.id,
            tool_id=job.tool_id,
            tool_type=tool_type,
            status=job.status,
            input=job.input,
            result=job.result,
            created_at=job.created_at,
            credits_used=job.credits_used,
        )

    async def delete_job(
        self,
        session: AsyncSession,
        job_id: UUID,
        user_id: UUID,
    ) -> None:
        deleted = await self.repository.delete(session, job_id, user_id)
        if not deleted:
            raise NotFoundError("Job", job_id)
        await session.commit()
