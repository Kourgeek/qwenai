"""gRPC client for the Catalog Service."""

from dataclasses import dataclass

import grpc

from src.config import settings


@dataclass(kw_only=True)
class ProductFilter:
    category: str | None = None
    status: str | None = None
    seller_id: str | None = None
    page: int = 1
    page_size: int = 50


async def get_product(product_id: str) -> dict | None:
    """Fetch a single product by ID from the Catalog Service."""
    async with grpc.aio.insecure_channel(f"{settings.catalog_service_host}:{settings.catalog_service_port}") as channel:
        # Placeholder: replace with the real stub call once the proto
        # definition for CatalogService is available.
        # Example target:
        #   stub = catalog_pb2_grpc.CatalogServiceStub(channel)
        #   resp = await stub.GetProduct(catalog_pb2.GetProductRequest(id=product_id))
        #   return _proto_to_dict(resp.product) if resp.HasField("product") else None
        return None


async def list_products(filters: ProductFilter | None = None) -> list[dict]:
    """List products with optional filters from the Catalog Service."""
    if filters is None:
        filters = ProductFilter()

    async with grpc.aio.insecure_channel(f"{settings.catalog_service_host}:{settings.catalog_service_port}") as channel:
        # Placeholder: replace with the real stub call.
        # Example target:
        #   stub = catalog_pb2_grpc.CatalogServiceStub(channel)
        #   resp = await stub.ListProducts(
        #       catalog_pb2.ListProductsRequest(
        #           category=filters.category,
        #           status=filters.status,
        #           seller_id=filters.seller_id,
        #           page=filters.page,
        #           page_size=filters.page_size,
        #       )
        #   )
        #   return [_proto_to_dict(p) for p in resp.products]
        return []
