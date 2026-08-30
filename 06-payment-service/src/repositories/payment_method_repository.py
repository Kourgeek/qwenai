"""
Async CRUD repository for PaymentMethod model.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.payment import PaymentMethod


class PaymentMethodRepository:
    """Data-access layer for the PaymentMethod aggregate."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, method: PaymentMethod) -> PaymentMethod:
        self._session.add(method)
        await self._session.flush()
        await self._session.refresh(method)
        return method

    async def get_by_id(self, method_id: UUID) -> PaymentMethod | None:
        stmt = select(PaymentMethod).where(PaymentMethod.id == method_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID) -> list[PaymentMethod]:
        stmt = select(PaymentMethod).where(PaymentMethod.user_id == user_id).order_by(PaymentMethod.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_default(self, user_id: UUID) -> PaymentMethod | None:
        stmt = (
            select(PaymentMethod)
            .where(PaymentMethod.user_id == user_id, PaymentMethod.is_default == 1)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


payment_method_repository = PaymentMethodRepository.__new__(PaymentMethodRepository)
