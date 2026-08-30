"""Business logic for the Order domain."""

from __future__ import annotations

import logging

from src.grpc_client.cart_client import get_cart
from src.grpc_client.catalog_client import get_product
from src.kafka.publisher import OrderKafkaPublisher
from src.models.order import Order, OrderItem
from src.repositories.order_item_repository import OrderItemRepository
from src.repositories.order_repository import OrderRepository

logger = logging.getLogger(__name__)

# ── Order status constants ────────────────────────────────────────────────
VALID_STATUSES = {"PENDING", "CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED"}
TRANSITION_MAP = {
    "PENDING": {"CONFIRMED", "CANCELLED"},
    "CONFIRMED": {"PROCESSING"},
    "PROCESSING": {"SHIPPED"},
    "SHIPPED": {"DELIVERED"},
}


class OrderService:
    """Orchestrates order lifecycle across repositories, gRPC clients, and Kafka."""

    def __init__(
        self,
        kafka_publisher: OrderKafkaPublisher,
    ) -> None:
        self._kafka = kafka_publisher

    # ── helpers ──────────────────────────────────────────────────────────

    async def _get_order_repo(self, session):
        return OrderRepository(session)

    async def _get_item_repo(self, session):
        return OrderItemRepository(session)

    # ── public API ───────────────────────────────────────────────────────

    async def create_order(
        self,
        session,
        user_id: int,
        cart_id: int,
        shipping_address: dict | None = None,
        payment_method: str | None = None,
    ) -> Order:
        """Validate the cart, build Order + OrderItems, persist and emit event."""
        order_repo = await self._get_order_repo(session)
        item_repo = await self._get_item_repo(session)

        # 1. Validate cart exists and is non-empty
        cart = await get_cart(user_id)
        if not cart or not cart.get("items"):
            raise ValueError("Cart is empty or does not exist")

        # 2. Build order
        total_amount = cart.get("total", 0.0)
        currency = cart.get("currency", "USD")
        order = Order(
            user_id=user_id,
            cart_id=cart_id,
            status="PENDING",
            total_amount=total_amount,
            currency=currency,
            shipping_address=shipping_address,
            payment_method=payment_method,
        )
        order = await order_repo.create(order)

        # 3. Build order items from cart
        items: list[OrderItem] = []
        for cart_item in cart.get("items", []):
            product = await get_product(cart_item["product_id"])
            item = OrderItem(
                order_id=order.id,
                product_id=cart_item["product_id"],
                product_name=product.get("name", ""),
                sku=product.get("sku", ""),
                quantity=cart_item["quantity"],
                unit_price=product.get("price", 0.0),
                total_price=product.get("price", 0.0) * cart_item["quantity"],
                image_url=product.get("image_url"),
            )
            items.append(item)

        await item_repo.create_batch(items)

        # 4. Emit domain event
        await self._kafka.publish_order_created(order.id, user_id, total_amount)

        logger.info("Order %s created for user %s", order.id, user_id)
        return order

    async def get_order(self, session, order_id: int) -> Order | None:
        order_repo = await self._get_order_repo(session)
        return await order_repo.get_by_id(order_id)

    async def get_user_orders(
        self,
        session,
        user_id: int,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Order]:
        order_repo = await self._get_order_repo(session)
        return await order_repo.get_by_user(user_id, limit=limit, offset=offset)

    async def cancel_order(
        self,
        session,
        order_id: int,
        user_id: int,
        reason: str | None = None,
    ) -> Order:
        """Cancel an order if it is still in a cancellable status."""
        order_repo = await self._get_order_repo(session)
        order = await order_repo.get_by_id(order_id)

        if order is None:
            raise LookupError(f"Order {order_id} not found")
        if order.user_id != user_id:
            raise PermissionError("User does not own this order")
        if order.status not in ("PENDING", "CONFIRMED"):
            raise ValueError(f"Cannot cancel order in status '{order.status}'")

        old_status = order.status
        order.status = "CANCELLED"
        order.cancelled_by = user_id
        order.cancellation_reason = reason
        await session.flush()

        await self._kafka.publish_order_status_changed(order_id, old_status, "CANCELLED")
        logger.info("Order %s cancelled by user %s", order_id, user_id)
        return order

    async def update_order_status(
        self,
        session,
        order_id: int,
        new_status: str,
    ) -> Order:
        """Transition an order to *new_status* following the state machine."""
        order_repo = await self._get_order_repo(session)
        order = await order_repo.get_by_id(order_id)

        if order is None:
            raise LookupError(f"Order {order_id} not found")
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{new_status}'")

        allowed = TRANSITION_MAP.get(order.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from '{order.status}' to '{new_status}'"
            )

        old_status = order.status
        order.status = new_status

        if new_status == "DELIVERED":
            from datetime import datetime, timezone

            order.completed_at = datetime.now(timezone.utc)
        elif new_status == "CANCELLED":
            from datetime import datetime, timezone

            order.cancelled_at = datetime.now(timezone.utc)

        await session.flush()

        await self._kafka.publish_order_status_changed(order_id, old_status, new_status)
        logger.info("Order %s status -> %s", order_id, new_status)
        return order
