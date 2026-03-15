from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobCreate(BaseModel):
    tool_id: UUID
    input: dict[str, Any]


class JobRead(BaseModel):
    id: UUID
    tool_id: UUID
    status: str
    input: dict[str, Any]
    result: dict[str, Any] | None
    created_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class JobStatus(BaseModel):
    id: UUID
    tool_id: UUID
    tool_type: str
    status: str
    input: dict[str, Any]
    result: dict[str, Any] | None
    created_at: datetime | None = None
    credits_used: int | None = None


class JobHistory(BaseModel):
    id: UUID
    tool_name: str
    tool_type: str
    tool_id: UUID
    status: str
    query: str
    title: str | None
    credits_used: int | None
    created_at: datetime
    completed_at: datetime | None
