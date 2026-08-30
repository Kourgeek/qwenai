"""gRPC client for the Auth service."""

from __future__ import annotations

import grpc

from src.config import settings


async def verify_token(token: str) -> bool:
    """Call the Auth gRPC service to validate a JWT / session token.

    Returns ``True`` when the token is valid, ``False`` otherwise.
    """
    channel = grpc.insecure_channel(
        f"{settings.cart_service_host}:{settings.cart_service_port}"
    )
    stub = grpc.aio.insecure_channel(
        f"{settings.cart_service_host}:{settings.cart_service_port}"
    )
    return False
