"""Cart business logic service.

Orchestrates catalog lookups, cart operations, and TTL management.
"""

from __future__ import annotations

import logging
from typing import Any

from src.grpc_client.catalog_client import get_product
from src.redis_client import CartRedisClient, cart_redis

logger = logging.getLogger(__name__)


class CartService:
    """Stateless service wrapping cart business rules."""

    def __init__(self, redis_client: CartRedisClient | None = None) -> None:
        self._redis = redis_client or cart_redis

    # -- read --------------------------------------------------------

    async def get_cart(self, user_id: str) -> dict[str, Any]:
        """Return the current cart for *user_id*.

        Returns an empty cart dict when the user has no cart.
        """
        cart = await self._redis.get_cart(user_id)
        if cart is None:
            return {"user_id": user_id, "items": [], "total": 0.0}
        return cart

    # -- mutations ---------------------------------------------------

    async def add_item(
        self,
        user_id: str,
        product_id: str,
        quantity: int,
    ) -> dict[str, Any]:
        """Add *quantity* of *product_id* to the cart.

        Validates the product exists via catalog-service first.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")

        product = await get_product(product_id)
        await self._redis.add_item(
            user_id=user_id,
            product_id=product_id,
            product_name=product["name"],
            unit_price=product["price"],
            quantity=quantity,
        )
        logger.info("AddItem user=%s product=%s qty=%d", user_id, product_id, quantity)
        return await self.get_cart(user_id)

    async def update_item(
        self,
        user_id: str,
        product_id: str,
        quantity: int,
    ) -> dict[str, Any]:
        """Update the quantity of *product_id* in the cart."""
        if quantity <= 0:
            # Delegate to remove_item path
            await self.remove_item(user_id, product_id)
            return await self.get_cart(user_id)

        # Validate product still exists
        await get_product(product_id)

        await self._redis.update_item(user_id=user_id, product_id=product_id, quantity=quantity)
        logger.info("UpdateItem user=%s product=%s qty=%d", user_id, product_id, quantity)
        return await self.get_cart(user_id)

    async def remove_item(self, user_id: str, product_id: str) -> dict[str, Any]:
        """Remove *product_id* from the cart."""
        cart_before = await self._redis.get_cart(user_id)
        if cart_before is None:
            raise KeyError(f"Cart for user '{user_id}' does not exist")

        item = next((i for i in cart_before["items"] if i["product_id"] == product_id), None)
        if item is None:
            raise KeyError(f"Product '{product_id}' not in cart for user '{user_id}'")

        await self._redis.remove_item(user_id=user_id, product_id=product_id)
        logger.info("RemoveItem user=%s product=%s", user_id, product_id)
        return await self.get_cart(user_id)

    async def clear_cart(self, user_id: str) -> dict[str, Any]:
        """Clear all items from the cart."""
        cart_before = await self._redis.get_cart(user_id)
        if cart_before is None:
            raise KeyError(f"Cart for user '{user_id}' does not exist")

        await self._redis.clear_cart(user_id=user_id)
        logger.info("ClearCart user=%s", user_id)
        return {"user_id": user_id, "items": [], "total": 0.0}

    async def save_for_later(
        self,
        user_id: str,
        product_id: str,
    ) -> dict[str, Any]:
        """Move *product_id* from cart to saved-for-later list."""
        cart = await self._redis.get_cart(user_id)
        if cart is None:
            raise KeyError(f"Cart for user '{user_id}' does not exist")

        item = next((i for i in cart["items"] if i["product_id"] == product_id), None)
        if item is None:
            raise KeyError(f"Product '{product_id}' not in cart for user '{user_id}'")

        await self._redis.save_for_later(
            user_id=user_id,
            product_id=item["product_id"],
            product_name=item["product_name"],
            unit_price=item["unit_price"],
            quantity=item["quantity"],
        )
        logger.info("SaveForLater user=%s product=%s", user_id, product_id)
        return await self.get_cart(user_id)

    async def move_to_cart(
        self,
        user_id: str,
        product_id: str,
    ) -> dict[str, Any]:
        """Move *product_id* from saved-for-later back to cart."""
        await self._redis.move_to_cart(user_id=user_id, product_id=product_id)
        logger.info("MoveToCart user=%s product=%s", user_id, product_id)
        return await self.get_cart(user_id)


# Singleton
cart_service = CartService()
