"""gRPC client for Payment service.

Handles payment-related queries via Payment service gRPC interface.
"""

import grpc
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PaymentGrpcClient:
    """Client for Payment service gRPC communication."""

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

    async def get_payment_methods(self, user_id: str) -> dict:
        """Fetch payment methods for a user.

        Args:
            user_id: The unique user identifier.

        Returns:
            Dict with payment methods list.

        Raises:
            grpc.aio.AioRpcError: If gRPC call fails.
        """
        if not self._channel:
            raise grpc.aio.AioRpcError(code=grpc.StatusCode.UNAVAILABLE)

        from src.grpc_client._payment_pb2 import GetPaymentMethodsRequest
        from src.grpc_client._payment_pb2_grpc import PaymentStub

        stub = PaymentStub(self._channel)
        try:
            response = await stub.GetPaymentMethods(
                GetPaymentMethodsRequest(user_id=user_id),
                timeout=5.0,
            )
            methods = [
                {
                    "method_id": m.method_id,
                    "type": m.type,
                    "last_four": m.last_four,
                    "is_default": m.is_default,
                }
                for m in response.methods
            ]
            return {"payment_methods": methods}
        except grpc.aio.AioRpcError as exc:
            logger.error("Payment gRPC call failed for user_id=%s: %s", user_id, exc)
            raise

    @property
    def is_connected(self) -> bool:
        return self._channel is not None and self._channel._connected
