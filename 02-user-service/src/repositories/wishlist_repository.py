"""Async repository for the WishlistItem model."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import WishlistItem


class WishlistRepository:
    """Data-access layer for ``WishlistItem``."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, item_id: uuid.UUID) -> WishlistItem | None:
        return await self._session.get(WishlistItem, item_id)

    async def get_by_product(self, user_id: uuid.UUID, product_id: str) -> WishlistItem | None:
        stmt = select(WishlistItem).where(
            WishlistItem.user_id == user_id,
            WishlistItem.product_id == product_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID) -> Sequence[WishlistItem]:
        stmt = select(WishlistItem).where(
            WishlistItem.user_id == user_id
        ).order_by(WishlistItem.added_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> WishlistItem:
        item = WishlistItem(**kwargs)
        self._session.add(item)
        await self._session.flush()
        await self._session.refresh(item)
        return item

    async def delete_by_product(self, user_id: uuid.UUID, product_id: str) -> bool:
        """Delete a single wishlist entry. Returns ``True`` if a row was removed."""
        stmt = (
            select(WishlistItem)
            .where(WishlistItem.user_id == user_id, WishlistItem.product_id == product_id)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        item = result.scalar_one_or_none()
        if item is None:
            return False
        await self._session.delete(item)
        await self._session.flush()
        return True
