"""Business logic for Wishlist operations."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import WishlistItem
from src.repositories.wishlist_repository import WishlistRepository

logger = logging.getLogger(__name__)


class WishlistService:
    """Orchestrates wishlist-level business logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = WishlistRepository(session)

    async def add_to_wishlist(
        self,
        user_id: uuid.UUID,
        product_id: str,
    ) -> WishlistItem:
        """Add *product_id* to the user's wishlist.

        Raises ``ValueError`` if the item is already present.
        """
        existing = await self._repo.get_by_product(user_id, product_id)
        if existing is not None:
            raise ValueError(
                f"Product {product_id} is already in user {user_id}'s wishlist"
            )
        item = await self._repo.create(user_id=user_id, product_id=product_id)
        logger.info("Product %s added to wishlist of user %s", product_id, user_id)
        return item

    async def get_wishlist(self, user_id: uuid.UUID) -> list[WishlistItem]:
        """Return all wishlist items for *user_id*."""
        return await self._repo.list_by_user(user_id)

    async def remove_from_wishlist(
        self,
        user_id: uuid.UUID,
        product_id: str,
    ) -> bool:
        """Remove a product from the wishlist.  Returns ``True`` if removed."""
        return await self._repo.delete_by_product(user_id, product_id)
