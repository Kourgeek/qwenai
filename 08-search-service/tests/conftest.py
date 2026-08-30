"""Shared test fixtures for the Search Service tests."""

from __future__ import annotations

from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_es_client() -> MagicMock:
    """Return a MagicMock that pretends to be ElasticsearchAsyncClient."""
    client = MagicMock()
    client.index_product = AsyncMock(return_value={"result": "updated"})
    client.search_products = AsyncMock(
        return_value={
            "hits": [
                {
                    "id": "1",
                    "name": "Test Product",
                    "description": "A test product",
                    "category": "electronics",
                    "brand": "TestBrand",
                    "price": 99.99,
                    "attributes": {},
                    "score": 1.0,
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 20,
        }
    )
    client.suggest_products = AsyncMock(return_value=["Test Product", "Test Product 2"])
    client.reindex_catalog = AsyncMock(return_value=1)
    client.health_check = AsyncMock(return_value={"status": "green", "cluster_name": "test"})
    client.connect = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_catalog_client() -> MagicMock:
    """Return a MagicMock that pretends to be CatalogServiceClient."""
    client = MagicMock()
    client.get_product = AsyncMock(
        return_value={
            "id": "1",
            "name": "Test Product",
            "description": "A test product",
            "category": "electronics",
            "brand": "TestBrand",
            "price": 99.99,
            "attributes": {"color": "black", "size": "M"},
        }
    )
    client.list_products = AsyncMock(
        return_value=[
            {
                "id": "1",
                "name": "Test Product",
                "description": "A test product",
                "category": "electronics",
                "brand": "TestBrand",
                "price": 99.99,
                "attributes": {"color": "black", "size": "M"},
            }
        ]
    )
    client.connect = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
async def search_service(
    mock_es_client: MagicMock, mock_catalog_client: MagicMock
) -> AsyncGenerator[MagicMock, None]:
    """Provide a SearchService instance with mocked dependencies."""
    # We need to import here to avoid circular imports at module level
    from src.services.search_service import SearchService

    service = SearchService(es_client=mock_es_client, catalog_client=mock_catalog_client)
    # Pre-connect the mocks
    await service.connect()
    yield service
    await service.close()
