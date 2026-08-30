"""SearchService — business logic layer for the Search Service."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Sequence

from src.config import settings
from src.es_client.client import ElasticsearchAsyncClient
from src.grpc_client.catalog_client import CatalogServiceClient

logger = logging.getLogger(__name__)


class SearchService:
    """Orchestrates ES operations and Catalog gRPC calls."""

    def __init__(
        self,
        es_client: ElasticsearchAsyncClient | None = None,
        catalog_client: CatalogServiceClient | None = None,
    ) -> None:
        self.es = es_client or ElasticsearchAsyncClient()
        self.catalog = catalog_client or CatalogServiceClient()

    # ── lifecycle ──────────────────────────────────────────────────────────

    async def connect(self) -> None:
        """Connect to ES and Catalog services."""
        await self.es.connect()
        await self.catalog.connect()

    async def close(self) -> None:
        """Disconnect from all services."""
        await self.es.close()
        await self.catalog.close()

    # ── search ─────────────────────────────────────────────────────────────

    async def search_products(
        self,
        query: str = "",
        categories: Sequence[str] | None = None,
        brands: Sequence[str] | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        sort_by: str = "_score",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """Execute a full-text search with optional filters, sorting, and pagination."""
        # Validate pagination
        page = max(1, page)
        page_size = max(1, min(page_size, 100))

        return await self.es.search_products(
            query=query,
            categories=categories,
            brands=brands,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )

    # ── suggest ────────────────────────────────────────────────────────────

    async def suggest_products(self, query: str, limit: int = 10) -> list[str]:
        """Return product name suggestions."""
        limit = max(1, min(limit, 50))
        return await self.es.suggest_products(query=query, limit=limit)

    # ── indexing ───────────────────────────────────────────────────────────

    async def index_product(self, product_id: str) -> dict[str, Any]:
        """Fetch a product from Catalog and index it into ES.

        Returns {"success": bool, "product_id": str, "message": str}.
        """
        product = await self.catalog.get_product(product_id)
        if product is None:
            return {"success": False, "product_id": product_id, "message": "Product not found in Catalog"}

        await self.es.index_product(product_id=product_id, product_data=product)
        return {"success": True, "product_id": product_id, "message": "Indexed successfully"}

    async def reindex_catalog(self, batch_size: int = 50) -> dict[str, Any]:
        """Bulk reindex all products from Catalog into ES.

        Returns {"success": bool, "indexed_count": int, "message": str}.
        """
        total_indexed = 0
        page = 1
        while True:
            products = await self.catalog.list_products(page=page, page_size=batch_size)
            if not products:
                break
            count = await self.es.reindex_catalog(products)
            total_indexed += count
            if len(products) < batch_size:
                break
            page += 1

        success = total_indexed > 0
        return {
            "success": success,
            "indexed_count": total_indexed,
            "message": f"Reindexed {total_indexed} products",
        }

    # ── health ─────────────────────────────────────────────────────────────

    async def health_check(self) -> dict[str, Any]:
        """Return health status of all downstream services."""
        es_status: dict[str, Any] = {"status": "unknown"}
        catalog_status: dict[str, Any] = {"status": "unknown"}

        try:
            es_health = await self.es.health_check()
            es_status = {
                "status": es_health.get("status", "unknown"),
                "cluster_name": es_health.get("cluster_name", ""),
            }
        except Exception as exc:
            es_status = {"status": "unreachable", "error": str(exc)}

        try:
            # Quick ping: try to get catalog info (lightweight call)
            products = await self.catalog.list_products(page=1, page_size=1)
            catalog_status = {"status": "ok" if products is not None else "error"}
        except Exception as exc:
            catalog_status = {"status": "unreachable", "error": str(exc)}

        overall = "healthy"
        if es_status["status"] not in ("green", "yellow") or catalog_status["status"] == "unreachable":
            overall = "degraded"
        if es_status["status"] == "unreachable" or catalog_status["status"] == "unreachable":
            overall = "unhealthy"

        return {
            "status": overall,
            "elasticsearch": es_status,
            "catalog_service": catalog_status,
        }
