"""
Async CRUD repository for Refund model.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.payment import Refund


class RefundRepository:
    """Data-access layer for the Refund aggregate."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, refund: Refund) -> Refund:
        self._session.add(refund)
        await self._session.flush()
        await self._session.refresh(refund)
        return refund

    async def get_by_id(self, refund_id: UUID) -> Refund | None:
        stmt = select(Refund).where(Refund.id == refund_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_payment_id(self, payment_id: UUID) -> list[Refund]:
        stmt = select(Refund).where(Refund.payment_id == payment_id).order_by(Refund.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        refund_id: UUID,
        status: str,
        provider_refund_id: str | None = None,
        refunded_at: datetime | None = None,
    ) -> Refund | None:
        stmt = select(Refund).where(Refund.id == refund_id).with_for_update()
        result = await self._session.execute(stmt)
        refund = result.scalar_one_or_none()
        if refund is None:
            return None
        refund.status = status
        if provider_refund_id is not None:
            refund.provider_refund_id = provider_refund_id
        if refunded_at is not None:
            refund.refunded_at = refunded_at
        await self._session.flush()
        await self._session.refresh(refund)
        return refund


refund_repository = RefundRepository.__new__(RefundRepository)
