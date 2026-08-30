"""Async Redis client for cart operations.

Provides a connection-pooled async Redis client with helper methods
for shopping-cart data structures stored as JSON.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as redis

from src.config import settings

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Key prefixes
# ------------------------------------------------------------------
CART_PREFIX = "cart"
SAVED_PREFIX = "saved_for_later"


def _cart_key(user_id: str) -> str:
    return f"{CART_PREFIX}:{user_id}"


def _saved_key(user_id: str) -> str:
    return f"{SAVED_PREFIX}:{user_id}"


class CartRedisClient:
    """Async Redis client specialised for cart data."""

    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    # -- lifecycle ---------------------------------------------------

    async def connect(self) -> None:
        """Establish connection pool."""
        self._client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True,
            ssl=False,
            max_connections=20,
            retry_on_timeout=True,
        )
        await self._client.ping()
        logger.info("Connected to Redis at %s:%s db=%s", settings.redis_host, settings.redis_port, settings.redis_db)

    async def close(self) -> None:
        """Shut down connection pool."""
        if self._client is not None:
            await self._client.close()
            self._client = None

    # -- public helpers ----------------------------------------------

    async def get_cart(self, user_id: str) -> dict[str, Any] | None:
        """Return the full cart dict for *user_id*, or ``None``."""
        data = await self._client.get(_cart_key(user_id))  # type: ignore[union-attr]
        if data is None:
            return None
        return json.loads(data)

    async def set_cart(self, user_id: str, cart: dict[str, Any], ttl: int | None = None) -> None:
        """Overwrite the cart for *user_id* with full *cart* dict."""
        key = _cart_key(user_id)
        ttl = ttl or settings.redis_cart_ttl
        await self._client.set(key, json.dumps(cart), ex=ttl)  # type: ignore[union-attr]

    async def add_item(self, user_id: str, product_id: str, product_name: str, unit_price: float, quantity: int) -> None:
        """Add or increment an item in the cart.

        Merges into the existing cart JSON and applies TTL.
        """
        key = _cart_key(user_id)
        raw = await self._client.get(key)  # type: ignore[union-attr]
        if raw:
            cart: dict[str, Any] = json.loads(raw)
        else:
            cart = {"items": [], "total": 0.0}

        # Find or create item entry
        item = next((i for i in cart["items"] if i["product_id"] == product_id), None)
        if item:
            item["quantity"] += quantity
        else:
            item = {
                "product_id": product_id,
                "product_name": product_name,
                "unit_price": unit_price,
                "quantity": quantity,
            }
            cart["items"].append(item)

        cart["total"] = round(sum(i["unit_price"] * i["quantity"] for i in cart["items"]), 2)
        await self._client.set(key, json.dumps(cart), ex=settings.redis_cart_ttl)  # type: ignore[union-attr]

    async def update_item(self, user_id: str, product_id: str, quantity: int) -> None:
        """Update the quantity of an item.  Sets to ``None`` if quantity == 0."""
        key = _cart_key(user_id)
        raw = await self._client.get(key)  # type: ignore[union-attr]
        if raw is None:
            raise KeyError(f"Cart for user '{user_id}' does not exist")

        cart: dict[str, Any] = json.loads(raw)
        item = next((i for i in cart["items"] if i["product_id"] == product_id), None)
        if item is None:
            raise KeyError(f"Product '{product_id}' not in cart for user '{user_id}'")

        if quantity <= 0:
            cart["items"] = [i for i in cart["items"] if i["product_id"] != product_id]
        else:
            item["quantity"] = quantity

        cart["total"] = round(sum(i["unit_price"] * i["quantity"] for i in cart["items"]), 2)
        await self._client.set(key, json.dumps(cart), ex=settings.redis_cart_ttl)  # type: ignore[union-attr]

    async def remove_item(self, user_id: str, product_id: str) -> None:
        """Remove a single item from the cart."""
        await self.update_item(user_id, product_id, 0)

    async def clear_cart(self, user_id: str) -> None:
        """Delete the entire cart for *user_id*."""
        await self._client.delete(_cart_key(user_id))  # type: ignore[union-attr]

    async def save_for_later(self, user_id: str, product_id: str, product_name: str, unit_price: float, quantity: int) -> None:
        """Move an item from cart to the saved-for-later list."""
        # Remove from cart
        await self.update_item(user_id, product_id, 0)

        # Append to saved list
        saved_key = _saved_key(user_id)
        raw = await self._client.get(saved_key)  # type: ignore[union-attr]
        if raw:
            saved: list[dict[str, Any]] = json.loads(raw)
        else:
            saved = []

        item = next((i for i in saved if i["product_id"] == product_id), None)
        if item:
            item["quantity"] += quantity
        else:
            saved.append({
                "product_id": product_id,
                "product_name": product_name,
                "unit_price": unit_price,
                "quantity": quantity,
            })
        await self._client.set(saved_key, json.dumps(saved), ex=settings.redis_saved_ttl)  # type: ignore[union-attr]

    async def move_to_cart(self, user_id: str, product_id: str) -> None:
        """Move an item from saved-for-later back into the cart."""
        saved_key = _saved_key(user_id)
        raw = await self._client.get(saved_key)  # type: ignore[union-attr]
        if raw is None:
            raise KeyError(f"No saved items for user '{user_id}'")

        saved: list[dict[str, Any]] = json.loads(raw)
        item = next((i for i in saved if i["product_id"] == product_id), None)
        if item is None:
            raise KeyError(f"Product '{product_id}' not in saved list for user '{user_id}'")

        # Add to cart
        await self.add_item(
            user_id=user_id,
            product_id=item["product_id"],
            product_name=item["product_name"],
            unit_price=item["unit_price"],
            quantity=item["quantity"],
        )

        # Remove from saved
        saved = [i for i in saved if i["product_id"] != product_id]
        await self._client.set(saved_key, json.dumps(saved), ex=settings.redis_saved_ttl)  # type: ignore[union-attr]


# Singleton instance
cart_redis = CartRedisClient()
