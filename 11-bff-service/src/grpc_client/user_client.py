"""gRPC client for User service.

Handles user profile queries via User service gRPC interface.
"""

import grpc
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class UserGrpcClient:
    """Client for User service gRPC communication."""

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

    async def get_user_profile(self, user_id: str) -> dict:
        """Fetch user profile by user ID.

        Args:
            user_id: The unique user identifier.

        Returns:
            Dict with user profile fields.

        Raises:
            grpc.aio.AioRpcError: If gRPC call fails.
        """
        if not self._channel:
            raise grpc.aio.AioRpcError(code=grpc.StatusCode.UNAVAILABLE)

        from src.grpc_client._user_pb2 import GetProfileRequest
        from src.grpc_client._user_pb2_grpc import UserStub

        stub = UserStub(self._channel)
        try:
            response = await stub.GetProfile(
                GetProfileRequest(user_id=user_id),
                timeout=5.0,
            )
            return {
                "user_id": response.user_id,
                "email": response.email,
                "first_name": response.first_name,
                "last_name": response.last_name,
                "phone": response.phone,
                "avatar_url": response.avatar_url,
                "created_at": response.created_at,
                "is_verified": response.is_verified,
            }
        except grpc.aio.AioRpcError as exc:
            logger.error("User gRPC call failed for user_id=%s: %s", user_id, exc)
            raise

    @property
    def is_connected(self) -> bool:
        return self._channel is not None and self._channel._connected
