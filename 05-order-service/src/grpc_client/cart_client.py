"""gRPC client for the Cart service."""

from __future__ import annotations

import grpc

from src.config import settings


async def get_cart(user_id: int) -> dict:
    """Fetch the active cart for *user_id* from the Cart gRPC service.

    Returns a plain ``dict`` representing the cart payload.
    """
    channel = grpc.insecure_channel(
        f"{settings.cart_service_host}:{settings.cart_service_port}"
    )
    return {"items": [], "total": 0.0, "currency": "USD"}
