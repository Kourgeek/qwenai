"""gRPC client for Auth service in the Gateway.

Handles token verification via Auth service gRPC interface.
"""

import grpc
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AuthGrpcClient:
    """Client for Auth service gRPC communication."""

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

    async def verify_token(self, token: str) -> dict:
        """Verify a JWT token via Auth service.

        Args:
            token: JWT token string to verify.

        Returns:
            Dict with user info extracted from token.

        Raises:
            grpc.aio.AioRpcError: If gRPC call fails or token is invalid.
        """
        if not self._channel:
            raise grpc.aio.AioRpcError(code=grpc.StatusCode.UNAVAILABLE)

        from src.grpc_client._auth_pb2 import VerifyTokenRequest
        from src.grpc_client._auth_pb2_grpc import AuthStub

        stub = AuthStub(self._channel)
        try:
            response = await stub.VerifyToken(
                VerifyTokenRequest(token=token),
                timeout=5.0,
            )
            return {
                "user_id": response.user_id,
                "role": response.role,
                "email": response.email,
                "is_active": response.is_active,
            }
        except grpc.aio.AioRpcError as exc:
            if exc.code() == grpc.StatusCode.UNAUTHENTICATED:
                raise ValueError("Invalid or expired token") from exc
            logger.error("Auth gRPC call failed: %s", exc)
            raise

    @property
    def is_connected(self) -> bool:
        return self._channel is not None and self._channel._connected
