"""Tests for SearchService business logic."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.services.search_service import SearchService


# ── search_products ──────────────────────────────────────────────────────────


class TestSearchProducts:
    """Tests for the search_products method."""

    @pytest.mark.asyncio
    async def test_search_products_returns_hits(self, search_service: MagicMock):
        result = await search_service.search_products(query="test")
        assert "hits" in result
        assert "total" in result
        assert "page" in result
        assert "page_size" in result
        assert len(result["hits"]) == 1
        assert result["hits"][0]["name"] == "Test Product"

    @pytest.mark.asyncio
    async def test_search_products_passes_filters(self, search_service: MagicMock):
        await search_service.search_products(
            query="laptop",
            categories=["electronics"],
            brands=["TestBrand"],
            min_price=50.0,
            max_price=200.0,
        )
        search_service.es.search_products.assert_called_once()
        call_kwargs = search_service.es.search_products.call_args[1]
        assert call_kwargs["query"] == "laptop"
        assert call_kwargs["categories"] == ["electronics"]
        assert call_kwargs["brands"] == ["TestBrand"]
        assert call_kwargs["min_price"] == 50.0
        assert call_kwargs["max_price"] == 200.0

    @pytest.mark.asyncio
    async def test_search_products_pagination(self, search_service: MagicMock):
        await search_service.search_products(query="test", page=2, page_size=10)
        call_kwargs = search_service.es.search_products.call_args[1]
        assert call_kwargs["page"] == 2
        assert call_kwargs["page_size"] == 10

    @pytest.mark.asyncio
    async def test_search_products_clamps_page_size(self, search_service: MagicMock):
        await search_service.search_products(query="test", page_size=200)
        call_kwargs = search_service.es.search_products.call_args[1]
        assert call_kwargs["page_size"] == 100  # clamped to max

    @pytest.mark.asyncio
    async def test_search_products_defaults(self, search_service: MagicMock):
        await search_service.search_products()
        call_kwargs = search_service.es.search_products.call_args[1]
        assert call_kwargs["query"] == ""
        assert call_kwargs["page"] == 1
        assert call_kwargs["page_size"] == 20
        assert call_kwargs["sort_by"] == "_score"
        assert call_kwargs["sort_order"] == "desc"


# ── suggest_products ─────────────────────────────────────────────────────────


class TestSuggestProducts:
    """Tests for the suggest_products method."""

    @pytest.mark.asyncio
    async def test_suggest_products_returns_list(self, search_service: MagicMock):
        result = await search_service.suggest_products(query="test")
        assert isinstance(result, list)
        assert len(result) == 2
        assert "Test Product" in result

    @pytest.mark.asyncio
    async def test_suggest_products_respects_limit(self, search_service: MagicMock):
        result = await search_service.suggest_products(query="test", limit=1)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_suggest_products_clamps_limit(self, search_service: MagicMock):
        result = await search_service.suggest_products(query="test", limit=100)
        assert len(result) <= 50  # clamped to max

    @pytest.mark.asyncio
    async def test_suggest_products_delegates_to_es(self, search_service: MagicMock):
        await search_service.suggest_products(query="laptop", limit=5)
        search_service.es.suggest_products.assert_called_once_with(query="laptop", limit=5)


# ── index_product ────────────────────────────────────────────────────────────


class TestIndexProduct:
    """Tests for the index_product method."""

    @pytest.mark.asyncio
    async def test_index_product_success(self, search_service: MagicMock):
        result = await search_service.index_product("1")
        assert result["success"] is True
        assert result["product_id"] == "1"
        search_service.catalog.get_product.assert_called_once_with("1")
        search_service.es.index_product.assert_called_once()

    @pytest.mark.asyncio
    async def test_index_product_not_found(self, search_service: MagicMock):
        search_service.catalog.get_product = AsyncMock(return_value=None)
        result = await search_service.index_product("999")
        assert result["success"] is False
        assert "not found" in result["message"].lower()
        search_service.es.index_product.assert_not_called()


# ── reindex_catalog ──────────────────────────────────────────────────────────


class TestReindexCatalog:
    """Tests for the reindex_catalog method."""

    @pytest.mark.asyncio
    async def test_reindex_catalog_success(self, search_service: MagicMock):
        result = await search_service.reindex_catalog(batch_size=50)
        assert result["success"] is True
        assert result["indexed_count"] == 1
        search_service.catalog.list_products.assert_called_once()
        search_service.es.reindex_catalog.assert_called_once()

    @pytest.mark.asyncio
    async def test_reindex_catalog_uses_batch_size(self, search_service: MagicMock):
        await search_service.reindex_catalog(batch_size=100)
        call_kwargs = search_service.catalog.list_products.call_args[1]
        assert call_kwargs["page_size"] == 100

    @pytest.mark.asyncio
    async def test_reindex_catalog_pagination(self, search_service: MagicMock):
        """Test that reindex_catalog fetches multiple pages."""
        # Simulate 3 pages of products
        call_count = [0]
        async def side_effect(page, page_size):
            call_count[0] += 1
            if call_count[0] <= 2:
                return [{"id": str(page), "name": f"Product {page}"}]
            return []

        search_service.catalog.list_products = AsyncMock(side_effect=side_effect)
        search_service.es.reindex_catalog = AsyncMock(return_value=1)

        result = await search_service.reindex_catalog(batch_size=1)
        assert result["indexed_count"] == 2
        assert call_count[0] == 3  # 2 pages of data + 1 empty page

    @pytest.mark.asyncio
    async def test_reindex_catalog_empty_catalog(self, search_service: MagicMock):
        search_service.catalog.list_products = AsyncMock(return_value=[])
        result = await search_service.reindex_catalog(batch_size=50)
        assert result["success"] is False
        assert result["indexed_count"] == 0
        search_service.es.reindex_catalog.assert_not_called()


# ── health_check ─────────────────────────────────────────────────────────────


class TestHealthCheck:
    """Tests for the health_check method."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, search_service: MagicMock):
        search_service.es.health_check = AsyncMock(
            return_value={"status": "green", "cluster_name": "test"}
        )
        search_service.catalog.list_products = AsyncMock(return_value=[{"id": "1"}])

        result = await search_service.health_check()
        assert result["status"] == "healthy"
        assert result["elasticsearch"]["status"] == "green"

    @pytest.mark.asyncio
    async def test_health_check_degraded(self, search_service: MagicMock):
        search_service.es.health_check = AsyncMock(
            return_value={"status": "yellow", "cluster_name": "test"}
        )
        search_service.catalog.list_products = AsyncMock(return_value=[{"id": "1"}])

        result = await search_service.health_check()
        assert result["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_health_check_unhealthy_es(self, search_service: MagicMock):
        search_service.es.health_check = AsyncMock(side_effect=RuntimeError("connection refused"))
        search_service.catalog.list_products = AsyncMock(return_value=[{"id": "1"}])

        result = await search_service.health_check()
        assert result["status"] == "unhealthy"
        assert result["elasticsearch"]["status"] == "unreachable"
