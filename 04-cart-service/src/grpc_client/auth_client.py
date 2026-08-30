"""gRPC client for the Auth service.

Connects to auth-service to verify JWT tokens via gRPC.
"""

from __future__ import annotations

import grpc

from src.config import settings

# ------------------------------------------------------------------
# Proto imports — generated stubs live alongside this package.
# ------------------------------------------------------------------
from src.grpc_client import cart_pb2_grpc  # type: ignore[attr-defined]  # noqa: E501

# Auth service stub type (generated from auth.proto)
# We use Protocol for static typing without importing the real proto.
AuthStub = cart_pb2_grpc.AuthServiceStub  # type: ignore[misc]


def _get_channel() -> grpc.aio.Channel:
    """Build an async gRPC channel to auth-service."""
    target = f"{settings.auth_service_host}:{settings.auth_service_port}"
    return grpc.aio.insecure_channel(target)


async def verify_token(token: str) -> bool:
    """Verify a JWT token by calling auth-service.

    Args:
        token: Raw JWT string to verify.

    Returns:
        True if the token is valid, False otherwise.

    Raises:
        grpc.aio.AioRpcError: On gRPC transport errors.
    """
    async with _get_channel() as channel:
        stub: AuthStub = cart_pb2_grpc.AuthServiceStub(channel)  # type: ignore[misc]
        request = cart_pb2_grpc.VerifyTokenRequest(token=token)  # type: ignore[attr-defined]
        response = await stub.VerifyToken(request)
        return response.valid
