from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.tool import ToolRepository
from app.schemas.tool import ToolRead


class ToolService:
    def __init__(self, repository: ToolRepository) -> None:
        self.repository = repository

    async def list_tools(self, session: AsyncSession) -> list[ToolRead]:
        tools = await self.repository.get_all(session)
        return [ToolRead.model_validate(t) for t in tools]

    async def get_tool(self, session: AsyncSession, tool_id: UUID) -> ToolRead:
        tool = await self.repository.get_by_id(session, tool_id)
        if tool is None:
            raise NotFoundError("Tool", tool_id)
        return ToolRead.model_validate(tool)
