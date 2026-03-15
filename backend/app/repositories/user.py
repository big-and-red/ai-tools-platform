import structlog
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = structlog.get_logger()


class UserRepository:
    async def get_by_id(self, session: AsyncSession, user_id: UUID) -> User | None:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_google_id(self, session: AsyncSession, google_id: str) -> User | None:
        result = await session.execute(select(User).where(User.google_id == google_id))
        return result.scalar_one_or_none()

    async def create_oauth_user(
        self, session: AsyncSession, email: str, google_id: str
    ) -> User:
        user = User(email=email, google_id=google_id)  # credits_balance uses model default
        session.add(user)
        await session.flush()
        return user

    async def deduct_credits(
        self, session: AsyncSession, user_id: UUID, amount: int
    ) -> None:
        """Atomically deduct credits. Balance may go negative (over-charge allowed)."""
        result = await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(credits_balance=User.credits_balance - amount)
            .returning(User.credits_balance)
        )
        if result.fetchone() is None:
            raise ValueError("User not found")

    async def refund_credits(
        self, session: AsyncSession, user_id: UUID, amount: int
    ) -> None:
        result = await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(credits_balance=User.credits_balance + amount)
            .returning(User.id)
        )
        if result.fetchone() is None:
            logger.warning("credits.refund.user_not_found", user_id=str(user_id), amount=amount)
