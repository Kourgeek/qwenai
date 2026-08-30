"""gRPC client for the Catalog service."""

import logging
from typing import Optional

import grpc

from src.config import settings

logger = logging.getLogger(__name__)

_CATALOG_CHANNEL: Optional[grpc.aio.Channel] = None


def _get_catalog_channel() -> grpc.aio.Channel:
    """Return a cached gRPC channel to the Catalog service."""
    global _CATALOG_CHANNEL
    if _CATALOG_CHANNEL is None:
        _CATALOG_CHANNEL = grpc.aio.insecure_channel(
            f"{settings.catalog_service_host}:{settings.catalog_service_port}"
        )
    return _CATALOG_CHANNEL


async def get_product(product_id: str) -> dict:
    """Fetch a single product by its ID from the Catalog service.

    Returns a plain ``dict`` representation of the product.
    """
    channel = _get_catalog_channel()
    from src.grpc_client._catalog_pb2 import GetProductRequest
    from src.grpc_client._catalog_pb2_grpc import CatalogStub

    stub = CatalogStub(channel)
    try:
        request = GetProductRequest(product_id=product_id)
        response = await stub.GetProduct(request, timeout=5.0)
        return {
            "id": str(response.id),
            "name": response.name,
            "description": response.description,
            "price": response.price,
            "category_id": str(response.category_id),
            "status": response.status,
        }
    except grpc.aio.AioRpcError as exc:
        logger.error("Catalog service gRPC error for product %s: %s", product_id, exc)
        return {}
    except Exception:  # noqa: BLE001
        logger.exception("Unexpected error fetching product %s", product_id)
        return {}


async def list_products_by_seller(seller_id: str) -> list[dict]:
    """Return all products belonging to *seller_id*.

    Products that are APPROVED are returned by default.
    """
    channel = _get_catalog_channel()
    from src.grpc_client._catalog_pb2 import ListProductsBySellerRequest
    from src.grpc_client._catalog_pb2_grpc import CatalogStub

    stub = CatalogStub(channel)
    try:
        request = ListProductsBySellerRequest(seller_id=seller_id)
        response = await stub.ListProductsBySeller(request, timeout=5.0)
        return [
            {
                "id": str(p.id),
                "seller_id": str(p.seller_id),
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "category_id": str(p.category_id),
                "status": p.status,
            }
            for p in response.products
        ]
    except grpc.aio.AioRpcError as exc:
        logger.error("Catalog service gRPC error for seller %s: %s", seller_id, exc)
        return []
    except Exception:  # noqa: BLE001
        logger.exception("Unexpected error listing products for seller %s", seller_id)
        return []
