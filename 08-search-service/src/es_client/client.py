"""Elasticsearch async client wrapper with connection pooling."""

from __future__ import annotations

import logging
from typing import Any, Sequence

from elasticsearch import AsyncElasticsearch

from src.config import settings

logger = logging.getLogger(__name__)


class ElasticsearchAsyncClient:
    """Thin async wrapper around ``elasticsearch.AsyncElasticsearch``.

    Manages the client lifecycle (init / close) and exposes high-level
    search, indexing, and reindex helpers.
    """

    def __init__(self) -> None:
        self._client: AsyncElasticsearch | None = None
        self._index: str = settings.es_index_name

    # ── lifecycle ──────────────────────────────────────────────────────────

    async def connect(self) -> None:
        """Create the underlying ``AsyncElasticsearch`` connection."""
        kwargs: dict[str, Any] = {
            "hosts": settings.es_hosts_list,
            "request_timeout": settings.es_request_timeout,
            "max_retries": settings.es_max_retries,
            "retry_on_timeout": True,
        }
        if settings.es_http_auth:
            kwargs["basic_auth"] = settings.es_http_auth
        if settings.es_api_key:
            kwargs["api_key"] = settings.es_api_key
        if settings.es_cloud_id:
            kwargs["cloud"] = {"id": settings.es_cloud_id}

        self._client = AsyncElasticsearch(**kwargs)
        logger.info(
            "Elasticsearch client connected to %s (index=%s)",
            settings.es_hosts_list,
            self._index,
        )

    async def close(self) -> None:
        """Gracefully shut down the connection pool."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Elasticsearch client disconnected")

    @property
    def client(self) -> AsyncElasticsearch:
        if self._client is None:
            raise RuntimeError("Elasticsearch client not connected. Call connect() first.")
        return self._client

    # ── public API ─────────────────────────────────────────────────────────

    async def index_product(self, product_id: str, product_data: dict[str, Any]) -> dict[str, Any]:
        """Index or update a single product document.

        Returns the ES response dict (``result``, ``_id``, ``_version``, …).
        """
        if not self._client:
            raise RuntimeError("Elasticsearch client not connected")

        resp = await self._client.index(
            index=self._index,
            id=product_id,
            document=product_data,
            refresh="wait_for",
        )
        logger.debug("Indexed product %s → result=%s", product_id, resp.get("result"))
        return resp

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
        """Run a full-text + filtered search.

        Returns ``{"hits": [...], "total": int, "page": int, "page_size": int}``.
        """
        if not self._client:
            raise RuntimeError("Elasticsearch client not connected")

        must: list[dict[str, Any]] = []

        # ── full-text on name + description ────────────────────────────────
        if query.strip():
            must.append({
                "multi_match": {
                    "query": query.strip(),
                    "fields": ["name^2", "description", "brand"],
                    "type": "best_fields",
                }
            })

        # ── category filter ────────────────────────────────────────────────
        if categories:
            must.append({"terms": {"category.keyword": categories}})

        # ── brand filter ───────────────────────────────────────────────────
        if brands:
            must.append({"terms": {"brand.keyword": brands}})

        # ── price range filter ─────────────────────────────────────────────
        range_filter: dict[str, Any] = {}
        if min_price is not None or max_price is not None:
            range_filter["gte"] = min_price
            range_filter["lte"] = max_price
            must.append({"range": {"price": range_filter}})

        body: dict[str, Any] = {
            "query": {"bool": {"must": must, "minimum_should_match": 1}},
            "from": (page - 1) * page_size,
            "size": page_size,
            "sort": [{"price": {"order": sort_order}}] if sort_by == "price" else [{"_score": {"order": sort_order}}],
        }

        resp = await self._client.search(index=self._index, body=body)

        hits = [
            {
                "id": hit["_source"].get("id", ""),
                "name": hit["_source"].get("name", ""),
                "description": hit["_source"].get("description", ""),
                "category": hit["_source"].get("category", ""),
                "brand": hit["_source"].get("brand", ""),
                "price": hit["_source"].get("price", 0.0),
                "attributes": hit["_source"].get("attributes", {}),
                "score": hit.get("_score"),
            }
            for hit in resp["hits"]["hits"]
        ]

        total = resp["hits"]["total"]
        if isinstance(total, dict):
            total = total["value"]

        return {
            "hits": hits,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def suggest_products(self, query: str, limit: int = 10) -> list[str]:
        """Return product name suggestions using a completion suggester.

        Falls back to a simple ``match_phrase_prefix`` auto-suggest.
        """
        if not self._client:
            raise RuntimeError("Elasticsearch client not connected")

        body = {
            "size": 0,
            "suggest": {
                "product-suggest": {
                    "prefix": query.strip(),
                    "completion": {
                        "field": "name_suggest",
                        "size": limit,
                    },
                }
            },
        }

        try:
            resp = await self._client.search(index=self._index, body=body)
            suggestions: list[str] = []
            for option in resp["suggest"]["product-suggest"][0].get("options", []):
                suggestions.append(option["_source"]["name"])
            return suggestions[:limit]
        except Exception:
            # Fallback: keyword prefix search on name
            fallback_body = {
                "query": {
                    "match_phrase_prefix": {"name": query.strip()}
                },
                "size": limit,
                "_source": ["name"],
            }
            resp = await self._client.search(index=self._index, body=fallback_body)
            return [
                hit["_source"]["name"]
                for hit in resp["hits"]["hits"]
            ][:limit]

    async def reindex_catalog(self, catalog_products: Sequence[dict[str, Any]]) -> int:
        """Bulk-index a list of product dicts from the Catalog service.

        Returns the number of documents successfully indexed.
        """
        if not self._client:
            raise RuntimeError("Elasticsearch client not connected")

        actions = [
            {
                "_index": self._index,
                "_id": str(p["id"]),
                "_source": p,
            }
            for p in catalog_products
        ]

        if not actions:
            return 0

        resp = await self._client.bulk(operations=actions, refresh="wait_for")

        if resp.get("errors"):
            # Log individual errors but still return partial count
            for item in resp["items"]:
                if "error" in item.get("index", {}):
                    logger.error("Bulk index error: %s", item["index"]["error"])
            indexed = sum(1 for i in resp["items"] if not i.get("index", {}).get("error"))
        else:
            indexed = len(actions)

        logger.info("Reindexed %d / %d products", indexed, len(actions))
        return indexed

    async def health_check(self) -> dict[str, Any]:
        """Return ES cluster health summary."""
        if not self._client:
            raise RuntimeError("Elasticsearch client not connected")
        return await self._client.cluster.health()
