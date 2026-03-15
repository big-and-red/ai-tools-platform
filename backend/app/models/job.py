from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    tool_id: Mapped[UUID] = mapped_column(ForeignKey("tools.id"), nullable=False)
    status: Mapped[str] = mapped_column(default="pending")  # pending | running | completed | failed
    input: Mapped[dict] = mapped_column(JSONB, nullable=False)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    title: Mapped[str | None] = mapped_column(nullable=True)
    credits_used: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
