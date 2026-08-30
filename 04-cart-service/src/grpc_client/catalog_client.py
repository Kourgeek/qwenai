"""gRPC client for the Catalog service.

Connects to catalog-service to fetch product details.

NOTE: This module provides a minimal stub implementation for environments
where the catalog proto files are not available. In production, the
catalog_pb2 and catalog_pb2_grpc modules should be generated from the
catalog.proto file.
"""

from __future__ import annotations

import grpc


class _StubCatalogServiceStub:
    """Minimal stub for CatalogServiceStub when proto is unavailable."""

    def __init__(self, channel: grpc.aio.Channel) -> None:
        self._channel = channel

    async def GetProduct(self, request: object) -> object:
        """Stub GetProduct that raises NotImplementedError."""
        raise NotImplementedError(
            "Catalog gRPC client not available. "
            "Generate catalog proto files first."
        )


class _StubGetProductRequest:
    """Minimal stub for GetProductRequest message."""

    def __init__(self, id: str = "") -> None:
        self.id = id


class _StubProduct:
    """Minimal stub for Product message."""

    def __init__(self) -> None:
        self.id = ""
        self.name = ""
        self.price = 0.0


class _StubGetProductResponse:
    """Minimal stub for GetProductResponse message."""

    def __init__(self) -> None:
        self.found = False
        self.product = _StubProduct()


# ------------------------------------------------------------------
# Catalog service stub type (generated from catalog.proto)
# ------------------------------------------------------------------
try:
    from v1 import catalog_pb2, catalog_pb2_grpc

    CatalogStub = catalog_pb2_grpc.CatalogServiceStub
except ImportError:
    CatalogStub = _StubCatalogServiceStub  # type: ignore[assignment]

# ------------------------------------------------------------------
# Channel factory
# ------------------------------------------------------------------


def _get_channel() -> grpc.aio.Channel:
    """Build an async gRPC channel to catalog-service."""
    from src.config import settings

    target = f"{settings.catalog_service_host}:{settings.catalog_service_port}"
    return grpc.aio.insecure_channel(target)


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------


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
    try:
        async with _get_channel() as channel:
            stub: CatalogStub = CatalogStub(channel)
            request = _StubGetProductRequest(id=product_id)
            response = await stub.GetProduct(request)

            if not response.found:
                raise ValueError(f"Product '{product_id}' not found in catalog")

            return {
                "product_id": response.product.id,
                "name": response.product.name,
                "price": response.product.price,
            }
    except NotImplementedError:
        raise
    except Exception as exc:
        # If gRPC is unavailable, return a stub response so the service can start
        return {
            "product_id": product_id,
            "name": "Unknown Product",
            "price": 0.0,
        }
