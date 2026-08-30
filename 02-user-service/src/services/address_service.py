"""Business logic for Address operations."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import Address
from src.repositories.address_repository import AddressRepository

logger = logging.getLogger(__name__)


class AddressService:
    """Orchestrates address-level business logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = AddressRepository(session)

    async def add_address(
        self,
        user_id: uuid.UUID,
        *,
        street: str,
        city: str,
        postal_code: str,
        country: str = "RU",
        state: str | None = None,
        is_default: bool = False,
        address_type: str = "shipping",
    ) -> Address:
        """Create and return a new address for *user_id*.

        If *is_default* is ``True``, all other defaults for that user
        are cleared first.
        """
        if is_default:
            await self._repo.unset_all_defaults(user_id)

        address = await self._repo.create(
            user_id=user_id,
            street=street,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            is_default=is_default,
            address_type=address_type,
        )
        logger.info("Address %s added for user %s", address.id, user_id)
        return address

    async def update_address(
        self,
        address_id: uuid.UUID,
        *,
        street: str | None = None,
        city: str | None = None,
        state: str | None = None,
        postal_code: str | None = None,
        country: str | None = None,
        is_default: bool | None = None,
    ) -> Address:
        """Update an existing address.  Returns the updated row."""
        address = await self._repo.get_by_id(address_id)
        if address is None:
            raise ValueError(f"Address {address_id} not found")

        update_kwargs = {k: v for k, v in locals().items() if k != "address_id" and v is not None}

        if is_default is True:
            await self._repo.unset_all_defaults(address.user_id)

        updated = await self._repo.update(address, **update_kwargs)
        logger.info("Address %s updated", address_id)
        return updated

    async def delete_address(self, address_id: uuid.UUID) -> None:
        """Delete an address.  Raises ``ValueError`` if not found."""
        address = await self._repo.get_by_id(address_id)
        if address is None:
            raise ValueError(f"Address {address_id} not found")
        await self._repo.delete(address)
        logger.info("Address %s deleted", address_id)

    async def list_addresses(self, user_id: uuid.UUID) -> list[Address]:
        """Return all addresses for *user_id*."""
        return await self._repo.list_by_user(user_id)

    async def set_default_address(
        self, address_id: uuid.UUID
    ) -> Address:
        """Mark *address_id* as the default.  Raises if not found."""
        address = await self._repo.get_by_id(address_id)
        if address is None:
            raise ValueError(f"Address {address_id} not found")
        updated = await self._repo.update(address, is_default=True)
        logger.info("Address %s set as default", address_id)
        return updated
