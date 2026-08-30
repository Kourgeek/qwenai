"""gRPC client for Order service.

Handles order queries via Order service gRPC interface.
"""

import grpc
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class OrderGrpcClient:
    """Client for Order service gRPC communication."""

    def __init__(self, target: str):
        self.target = target
        self._channel: Optional[grpc.aio.Channel] = None

    async def initialize(self) -> None:
        """Initialize the gRPC channel."""
        self._channel = grpc.aio.insecure_channel(
            self.target,
            options=[
                ("grpc.max_metadata_size", 65536),
                ("grpc.keepalive_time_ms", 10000),
                ("grpc.keepalive_timeout_ms", 5000),
            ],
        )

    async def close(self) -> None:
        """Close the gRPC channel."""
        if self._channel:
            await self._channel.close()
            self._channel = None

    async def get_user_orders(self, user_id: str, limit: int = 20, offset: int = 0) -> dict:
        """Fetch orders for a user.

        Args:
            user_id: The unique user identifier.
            limit: Max number of orders to return.
            offset: Pagination offset.

        Returns:
            Dict with orders list and pagination info.

        Raises:
            grpc.aio.AioRpcError: If gRPC call fails.
        """
        if not self._channel:
            raise grpc.aio.AioRpcError(code=grpc.StatusCode.UNAVAILABLE)

        from src.grpc_client._order_pb2 import GetUserOrdersRequest
        from src.grpc_client._order_pb2_grpc import OrderStub

        stub = OrderStub(self._channel)
        try:
            response = await stub.GetUserOrders(
                GetUserOrdersRequest(
                    user_id=user_id,
                    limit=limit,
                    offset=offset,
                ),
                timeout=10.0,
            )
            orders = [
                {
                    "order_id": o.order_id,
                    "status": o.status,
                    "total_amount": o.total_amount,
                    "currency": o.currency,
                    "created_at": o.created_at,
                    "items_count": o.items_count,
                }
                for o in response.orders
            ]
            return {
                "orders": orders,
                "total_count": response.total_count,
                "limit": limit,
                "offset": offset,
            }
        except grpc.aio.AioRpcError as exc:
            logger.error("Order gRPC call failed for user_id=%s: %s", user_id, exc)
            raise

    async def get_order(self, order_id: str) -> dict:
        """Fetch a single order by ID.

        Args:
            order_id: The unique order identifier.

        Returns:
            Dict with order details.

        Raises:
            grpc.aio.AioRpcError: If gRPC call fails.
        """
        if not self._channel:
            raise grpc.aio.AioRpcError(code=grpc.StatusCode.UNAVAILABLE)

        from src.grpc_client._order_pb2 import GetOrderRequest
        from src.grpc_client._order_pb2_grpc import OrderStub

        stub = OrderStub(self._channel)
        try:
            response = await stub.GetOrder(
                GetOrderRequest(order_id=order_id),
                timeout=5.0,
            )
            items = [
                {
                    "product_id": item.product_id,
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                }
                for item in response.items
            ]
            return {
                "order_id": response.order_id,
                "user_id": response.user_id,
                "status": response.status,
                "total_amount": response.total_amount,
                "currency": response.currency,
                "shipping_address": response.shipping_address,
                "items": items,
                "created_at": response.created_at,
                "updated_at": response.updated_at,
            }
        except grpc.aio.AioRpcError as exc:
            logger.error("Order gRPC call failed for order_id=%s: %s", order_id, exc)
            raise

    @property
    def is_connected(self) -> bool:
        return self._channel is not None and self._channel._connected
