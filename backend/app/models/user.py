from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(nullable=True)
    google_id: Mapped[str | None] = mapped_column(unique=True, nullable=True, index=True)
    credits_balance: Mapped[int] = mapped_column(default=500, server_default="500", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
