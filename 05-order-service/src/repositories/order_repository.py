"""Async CRUD repository for the Order model."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.order import Order


class OrderRepository:
    """Data-access layer for ``Order`` rows."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order)
        return order

    async def get_by_id(self, order_id: int) -> Order | None:
        return await self.session.get(Order, order_id)

    async def get_by_user(
        self, user_id: int, *, limit: int = 20, offset: int = 0
    ) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, order_id: int, new_status: str) -> Order | None:
        order = await self.get_by_id(order_id)
        if order is None:
            return None
        order.status = new_status
        await self.session.flush()
        await self.session.refresh(order)
        return order

    async def list(
        self, *, limit: int = 20, offset: int = 0, status: str | None = None
    ) -> list[Order]:
        query = select(Order).order_by(Order.created_at.desc()).limit(limit).offset(offset)
        if status:
            query = query.where(Order.status == status)
        result = await self.session.execute(query)
        return list(result.scalars().all())
