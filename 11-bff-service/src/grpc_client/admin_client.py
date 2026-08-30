"""gRPC client for Admin service.

Handles admin dashboard and management queries via Admin service gRPC interface.
"""

import grpc
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AdminGrpcClient:
    """Client for Admin service gRPC communication."""

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

    async def get_dashboard_stats(self) -> dict:
        """Fetch dashboard statistics.

        Returns:
            Dict with dashboard metrics.

        Raises:
            grpc.aio.AioRpcError: If gRPC call fails.
        """
        if not self._channel:
            raise grpc.aio.AioRpcError(code=grpc.StatusCode.UNAVAILABLE)

        from src.grpc_client._admin_pb2 import GetDashboardRequest
        from src.grpc_client._admin_pb2_grpc import AdminStub

        stub = AdminStub(self._channel)
        try:
            response = await stub.GetDashboard(
                GetDashboardRequest(),
                timeout=10.0,
            )
            return {
                "total_users": response.total_users,
                "total_sellers": response.total_sellers,
                "total_products": response.total_products,
                "total_orders": response.total_orders,
                "total_revenue": response.total_revenue,
                "revenue_currency": response.revenue_currency,
                "active_sessions": response.active_sessions,
                "recent_orders": [
                    {
                        "order_id": o.order_id,
                        "user_id": o.user_id,
                        "total_amount": o.total_amount,
                        "status": o.status,
                        "created_at": o.created_at,
                    }
                    for o in response.recent_orders
                ],
            }
        except grpc.aio.AioRpcError as exc:
            logger.error("Admin gRPC call failed: %s", exc)
            raise

    @property
    def is_connected(self) -> bool:
        return self._channel is not None and self._channel._connected
