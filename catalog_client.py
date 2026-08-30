"""gRPC client for the Catalog service.

Connects to catalog-service to fetch product details.
"""

from __future__ import annotations

import grpc

from src.config import settings

from v1 import catalog_pb2, catalog_pb2_grpc  # type: ignore[attr-defined]

# ------------------------------------------------------------------
# Catalog service stub type (generated from catalog.proto)
# ------------------------------------------------------------------
CatalogStub = catalog_pb2_grpc.CatalogServiceStub  # type: ignore[misc]


def _get_channel() -> grpc.aio.Channel:
    """Build an async gRPC channel to catalog-service."""
    target = f"{settings.catalog_service_host}:{settings.catalog_service_port}"
    return grpc.aio.insecure_channel(target)


async def get_product(product_id: str) -> dict:
    """Fetch product details by ID from the catalog service.

    Args:
        product_id: Unique product identifier.

    Returns:
        Dictionary with keys ``product_id``, ``name``, ``price``.

    Raises:
        grpc.aio.AioRpcError: On gRPC transport errors.
        ValueError: If the product is not found.
    """
    async with _get_channel() as channel:
        stub: CatalogStub = catalog_pb2_grpc.CatalogServiceStub(channel)  # type: ignore[misc]
        request = catalog_pb2.GetProductRequest(id=product_id)  # type: ignore[attr-defined]
        response = await stub.GetProduct(request)

        if not response.found:
            raise ValueError(f"Product '{product_id}' not found in catalog")

        return {
            "product_id": response.product.id,
            "name": response.product.name,
            "price": response.product.price,
        }
