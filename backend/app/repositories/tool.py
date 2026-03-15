from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool import Tool


class ToolRepository:
    async def get_all(self, session: AsyncSession) -> list[Tool]:
        result = await session.execute(
            select(Tool).where(Tool.is_active == True).order_by(Tool.created_at)  # noqa: E712
        )
        return list(result.scalars().all())

    async def get_by_id(self, session: AsyncSession, tool_id: UUID) -> Tool | None:
        result = await session.execute(select(Tool).where(Tool.id == tool_id))
        return result.scalar_one_or_none()
