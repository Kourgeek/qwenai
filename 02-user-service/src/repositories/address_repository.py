"""Async repository for the Address model."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import Address


class AddressRepository:
    """Data-access layer for ``Address``."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, address_id: uuid.UUID) -> Address | None:
        return await self._session.get(Address, address_id)

    async def list_by_user(self, user_id: uuid.UUID) -> Sequence[Address]:
        stmt = select(Address).where(
            Address.user_id == user_id
        ).order_by(Address.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_default(self, user_id: uuid.UUID) -> Address | None:
        stmt = select(Address).where(
            Address.user_id == user_id,
            Address.is_default.is_(True),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Address:
        address = Address(**kwargs)
        self._session.add(address)
        await self._session.flush()
        await self._session.refresh(address)
        return address

    async def update(self, address: Address, **kwargs) -> Address:
        for key, value in kwargs.items():
            if hasattr(address, key):
                setattr(address, key, value)
        await self._session.flush()
        await self._session.refresh(address)
        return address

    async def delete(self, address: Address) -> None:
        await self._session.delete(address)
        await self._session.flush()

    async def unset_all_defaults(self, user_id: uuid.UUID) -> None:
        """Set every default address for *user_id* to ``is_default=False``."""
        from sqlalchemy import update

        stmt = (
            update(Address)
            .where(Address.user_id == user_id, Address.is_default.is_(True))
            .values(is_default=False)
        )
        await self._session.execute(stmt)
        await self._session.flush()
