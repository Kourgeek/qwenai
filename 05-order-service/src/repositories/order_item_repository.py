"""Async CRUD repository for the OrderItem model."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.order import OrderItem


class OrderItemRepository:
    """Data-access layer for ``OrderItem`` rows."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_batch(self, items: list[OrderItem]) -> list[OrderItem]:
        self.session.add_all(items)
        await self.session.flush()
        for item in items:
            await self.session.refresh(item)
        return items

    async def get_by_order(self, order_id: int) -> list[OrderItem]:
        stmt = select(OrderItem).where(OrderItem.order_id == order_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
