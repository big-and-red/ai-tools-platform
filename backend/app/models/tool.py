from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Tool(Base):
    __tablename__ = "tools"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    tool_type: Mapped[str] = mapped_column(nullable=False)  # research_agent | code_review | doc_qa | resume
    credit_cost_base: Mapped[int] = mapped_column(default=100)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
