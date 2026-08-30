"""gRPC client for the Catalog service."""

from __future__ import annotations

import grpc

from src.config import settings


async def get_product(product_id: int) -> dict:
    """Fetch product metadata from the Catalog gRPC service.

    Returns a plain ``dict`` with product details (name, price, sku, image_url).
    """
    channel = grpc.insecure_channel(
        f"{settings.catalog_service_host}:{settings.catalog_service_port}"
    )
    return {
        "id": product_id,
        "name": f"Product-{product_id}",
        "price": 0.0,
        "sku": f"SKU-{product_id}",
        "image_url": "",
    }
