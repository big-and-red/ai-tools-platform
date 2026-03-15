from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ToolType(str, Enum):
    research_agent = "research_agent"
    code_review = "code_review"
    doc_qa = "doc_qa"
    resume = "resume"


class ToolRead(BaseModel):
    id: UUID
    name: str
    description: str
    tool_type: ToolType
    credit_cost_base: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ToolCreate(BaseModel):
    name: str
    description: str
    tool_type: ToolType
    credit_cost_base: int = 100
