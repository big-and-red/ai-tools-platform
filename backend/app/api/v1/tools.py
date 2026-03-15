from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.containers import Container
from app.core.database import get_db
from app.schemas.tool import ToolRead
from app.services.tool import ToolService

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("", response_model=list[ToolRead])
@inject
async def list_tools(
    session: AsyncSession = Depends(get_db),
    service: ToolService = Depends(Provide[Container.tool_service]),
) -> list[ToolRead]:
    return await service.list_tools(session)


@router.get("/{tool_id}", response_model=ToolRead)
@inject
async def get_tool(
    tool_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: ToolService = Depends(Provide[Container.tool_service]),
) -> ToolRead:
    return await service.get_tool(session, tool_id)
