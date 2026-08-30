"""gRPC client for Cart service.

Handles shopping cart operations via Cart service gRPC interface.
"""

import grpc
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CartGrpcClient:
    """Client for Cart service gRPC communication."""

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

    async def get_cart(self, user_id: str) -> dict:
        """Fetch the shopping cart for a user.

        Args:
            user_id: The unique user identifier.

        Returns:
            Dict with cart items and totals.

        Raises:
            grpc.aio.AioRpcError: If gRPC call fails.
        """
        if not self._channel:
            raise grpc.aio.AioRpcError(code=grpc.StatusCode.UNAVAILABLE)

        from src.grpc_client._cart_pb2 import GetCartRequest
        from src.grpc_client._cart_pb2_grpc import CartStub

        stub = CartStub(self._channel)
        try:
            response = await stub.GetCart(
                GetCartRequest(user_id=user_id),
                timeout=5.0,
            )
            items = [
                {
                    "product_id": item.product_id,
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "subtotal": item.subtotal,
                }
                for item in response.items
            ]
            return {
                "cart_id": response.cart_id,
                "user_id": response.user_id,
                "items": items,
                "total_items": response.total_items,
                "total_amount": response.total_amount,
                "currency": response.currency,
            }
        except grpc.aio.AioRpcError as exc:
            logger.error("Cart gRPC call failed for user_id=%s: %s", user_id, exc)
            raise

    @property
    def is_connected(self) -> bool:
        return self._channel is not None and self._channel._connected
