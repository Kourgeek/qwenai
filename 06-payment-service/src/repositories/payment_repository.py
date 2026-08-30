"""
Async CRUD repository for Payment model.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.payment import Payment, PaymentProvider, PaymentStatus


class PaymentRepository:
    """Data-access layer for the Payment aggregate."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, payment: Payment) -> Payment:
        self._session.add(payment)
        await self._session.flush()
        await self._session.refresh(payment)
        return payment

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        stmt = select(Payment).where(Payment.id == payment_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_order_id(self, order_id: str) -> Payment | None:
        stmt = select(Payment).where(Payment.order_id == order_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_provider_payment_id(self, provider_payment_id: str) -> Payment | None:
        stmt = select(Payment).where(Payment.provider_payment_id == provider_payment_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID, limit: int = 50, offset: int = 0) -> list[Payment]:
        stmt = (
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        payment_id: UUID,
        status: PaymentStatus,
        provider_payment_id: str | None = None,
        provider_error: str | None = None,
        paid_at: datetime | None = None,
    ) -> Payment | None:
        stmt = select(Payment).where(Payment.id == payment_id).with_for_update()
        result = await self._session.execute(stmt)
        payment = result.scalar_one_or_none()
        if payment is None:
            return None
        payment.status = status
        if provider_payment_id is not None:
            payment.provider_payment_id = provider_payment_id
        if provider_error is not None:
            payment.provider_error = provider_error
        if paid_at is not None:
            payment.paid_at = paid_at
        await self._session.flush()
        await self._session.refresh(payment)
        return payment

    async def update(self, payment: Payment) -> Payment:
        self._session.add(payment)
        await self._session.flush()
        await self._session.refresh(payment)
        return payment

    async def get_by_id_with_methods(self, payment_id: UUID) -> Payment | None:
        stmt = (
            select(Payment)
            .options(selectinload(Payment.payment_method))
            .where(Payment.id == payment_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


payment_repository = PaymentRepository.__new__(PaymentRepository)  # type: ignore[arg-type]
# Note: instantiated per-request via dependency injection; this placeholder
# prevents import-time errors.
