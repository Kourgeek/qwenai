"""gRPC client for the Auth service."""

import logging
from typing import Optional

import grpc

from src.config import settings

logger = logging.getLogger(__name__)

_AUTH_CHANNEL: Optional[grpc.aio.Channel] = None


def _get_auth_channel() -> grpc.aio.Channel:
    """Return a cached gRPC channel to the Auth service."""
    global _AUTH_CHANNEL
    if _AUTH_CHANNEL is None:
        _AUTH_CHANNEL = grpc.aio.insecure_channel(
            f"{settings.auth_service_host}:{settings.auth_service_port}"
        )
    return _AUTH_CHANNEL


async def verify_token(token: str) -> bool:
    """Verify a JWT/access token via the Auth service.

    Returns ``True`` when the token is valid, ``False`` otherwise.
    """
    if not token:
        return False

    channel = _get_auth_channel()
    # Lazy import to avoid circular dependency at module level
    from src.grpc_client._auth_pb2 import VerifyTokenRequest
    from src.grpc_client._auth_pb2_grpc import AuthStub

    stub = AuthStub(channel)
    try:
        request = VerifyTokenRequest(token=token)
        response = await stub.VerifyToken(request, timeout=5.0)
        return bool(response.valid)
    except grpc.aio.AioRpcError as exc:
        logger.error("Auth service gRPC error: %s", exc)
        return False
    except Exception:  # noqa: BLE001
        logger.exception("Unexpected error while verifying token")
        return False
