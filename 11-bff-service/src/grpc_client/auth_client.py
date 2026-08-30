"""gRPC client for Auth service.

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
        # Verify channel is ready
        try:
            await grpc.aio.channel(self.target).get_channel().channel().ready()
        except Exception:
            logger.warning("Could not verify gRPC channel readiness for %s", self.target)

    async def close(self) -> None:
        """Close the gRPC channel."""
        if self._channel:
            await self._channel.close()
            self._channel = None

    async def verify_token(self, token: str) -> dict:
        """Verify a JWT token via Auth service."""
        if not self._channel or not self._channel._connected:
            raise grpc.aio.AioRpcError(code=grpc.StatusCode.UNAVAILABLE)

        from auth.v1 import auth_pb2, auth_pb2_grpc

        stub = auth_pb2_grpc.AuthServiceStub(self._channel)
        try:
            response = await stub.VerifyToken(
                auth_pb2.VerifyTokenRequest(token=token),
                timeout=5.0,
            )
            return {
                "user_id": response.user_id,
                "role": response.role,
                "email": response.email,
                "is_active": response.is_active,
            }
        except grpc.aio.AioRpcError as exc:
            logger.error("Auth gRPC call failed: %s", exc)
            raise

    async def login(self, email: str, password: str) -> dict:
        """Authenticate user via auth service gRPC."""
        if not self._channel:
            raise grpc.aio.AioRpcError(code=grpc.StatusCode.UNAVAILABLE)

        from auth.v1 import auth_pb2, auth_pb2_grpc

        stub = auth_pb2_grpc.AuthServiceStub(self._channel)
        response = await stub.Login(
            auth_pb2.LoginRequest(email=email, password=password),
            timeout=5.0,
        )
        return {
            "user_id": response.user_id,
            "email": response.email,
            "access_token": response.access_token,
            "refresh_token": response.refresh_token,
        }

    async def register(self, email: str, password: str, first_name: str = "", last_name: str = "") -> dict:
        """Register a new user via auth service gRPC."""
        if not self._channel:
            raise grpc.aio.AioRpcError(code=grpc.StatusCode.UNAVAILABLE)

        from auth.v1 import auth_pb2, auth_pb2_grpc

        stub = auth_pb2_grpc.AuthServiceStub(self._channel)
        response = await stub.Register(
            auth_pb2.RegisterRequest(email=email, password=password, first_name=first_name, last_name=last_name),
            timeout=5.0,
        )
        return {
            "user_id": response.user_id,
            "email": response.email,
            "access_token": response.access_token,
            "refresh_token": response.refresh_token,
        }

    async def refresh(self, refresh_token: str) -> dict:
        """Refresh access token via auth service gRPC."""
        if not self._channel:
            raise grpc.aio.AioRpcError(code=grpc.StatusCode.UNAVAILABLE)

        from auth.v1 import auth_pb2, auth_pb2_grpc

        stub = auth_pb2_grpc.AuthServiceStub(self._channel)
        response = await stub.Refresh(
            auth_pb2.RefreshRequest(refresh_token=refresh_token),
            timeout=5.0,
        )
        return {
            "access_token": response.access_token,
            "refresh_token": response.refresh_token,
        }

    async def logout(self, refresh_token: str) -> None:
        """Logout and invalidate token via auth service gRPC."""
        if not self._channel:
            raise grpc.aio.AioRpcError(code=grpc.StatusCode.UNAVAILABLE)

        from auth.v1 import auth_pb2, auth_pb2_grpc

        stub = auth_pb2_grpc.AuthServiceStub(self._channel)
        await stub.Logout(
            auth_pb2.LogoutRequest(refresh_token=refresh_token),
            timeout=5.0,
        )

    async def forgot_password(self, email: str) -> dict:
        """Request password reset via auth service."""
        if not self._channel:
            raise grpc.aio.AioRpcError(code=grpc.StatusCode.UNAVAILABLE)

        from auth.v1 import auth_pb2, auth_pb2_grpc

        stub = auth_pb2_grpc.AuthServiceStub(self._channel)
        response = await stub.ForgotPassword(
            auth_pb2.ForgotPasswordRequest(email=email),
            timeout=5.0,
        )
        return {
            "email": response.email,
            "reset_token": response.reset_token,
        }

    @property
    def is_connected(self) -> bool:
        return self._channel is not None and self._channel._connected
