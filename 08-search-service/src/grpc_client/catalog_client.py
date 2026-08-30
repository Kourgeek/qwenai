"""Async gRPC client for the Catalog service."""

from __future__ import annotations

import logging
from typing import Any

import grpc

from src.config import settings

logger = logging.getLogger(__name__)


class CatalogServiceClient:
    """Thin async wrapper around the Catalog gRPC service stub."""

    def __init__(self) -> None:
        self._channel: grpc.aio.Channel | None = None
        self._stub: Any = None

    # ── lifecycle ──────────────────────────────────────────────────────────

    async def connect(self) -> None:
        """Create the gRPC channel and stub."""
        self._channel = grpc.aio.insecure_channel(
            f"{settings.catalog_service_host}:{settings.catalog_service_port}",
            options=[
                ("grpc.max_send_message_length", 50 * 1024 * 1024),
                ("grpc.max_receive_message_length", 50 * 1024 * 1024),
            ],
        )
        # Import here to avoid circular imports
        from src.grpc_server.search_pb2_grpc import CatalogServiceStub

        self._stub = CatalogServiceStub(self._channel)
        logger.info(
            "Catalog gRPC channel created → %s:%s",
            settings.catalog_service_host,
            settings.catalog_service_port,
        )

    async def close(self) -> None:
        """Close the gRPC channel."""
        if self._channel:
            await self._channel.close()
            self._channel = None
            self._stub = None
            logger.info("Catalog gRPC channel closed")

    # ── public API ─────────────────────────────────────────────────────────

    async def get_product(self, product_id: str) -> dict[str, Any] | None:
        """Fetch a single product by ID from the Catalog service."""
        if not self._stub:
            raise RuntimeError("Catalog client not connected. Call connect() first.")

        from src.grpc_server.search_pb2 import ProductId

        try:
            response = await self._stub.GetProduct(ProductId(id=product_id))
            if response.HasField("product"):
                return self._parse_product(response.product)
            return None
        except grpc.aio.AioRpcError as exc:
            logger.warning("Catalog GetProduct(%s) failed: %s", product_id, exc)
            return None

    async def list_products(self, page: int = 1, page_size: int = 100) -> list[dict[str, Any]]:
        """Retrieve products from the Catalog service (paginated)."""
        if not self._stub:
            raise RuntimeError("Catalog client not connected. Call connect() first.")

        from src.grpc_server.search_pb2 import ListProductsRequest

        try:
            response = await self._stub.ListProducts(
                ListProductsRequest(page=page, page_size=page_size)
            )
            return [self._parse_product(p) for p in response.products]
        except grpc.aio.AioRpcError as exc:
            logger.warning("Catalog ListProducts(page=%d) failed: %s", page, exc)
            return []

    # ── helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_product(pb_product: Any) -> dict[str, Any]:
        """Convert a protobuf Product message to a plain dict."""
        return {
            "id": pb_product.id,
            "name": pb_product.name,
            "description": pb_product.description,
            "category": pb_product.category,
            "brand": pb_product.brand,
            "price": pb_product.price,
            "attributes": dict(pb_product.attributes) if pb_product.attributes else {},
        }
