"""Shared pytest fixtures for Cart Service tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

import pytest


@pytest.fixture(autouse=True)
def mock_redis():
    """Provide a fully-mocked CartRedisClient."""
    mock_client = AsyncMock()
    mock_client.get_cart = AsyncMock(return_value={"items": [], "total": 0.0})
    mock_client.set_cart = AsyncMock()
    mock_client.add_item = AsyncMock()
    mock_client.update_item = AsyncMock()
    mock_client.remove_item = AsyncMock()
    mock_client.clear_cart = AsyncMock()
    mock_client.save_for_later = AsyncMock()
    mock_client.move_to_cart = AsyncMock()
    mock_client.connect = AsyncMock()
    mock_client.close = AsyncMock()

    with patch("src.redis_client.cart_redis", mock_client):
        with patch("src.services.cart_service.cart_service", MagicMock()):
            yield mock_client


@pytest.fixture
def mock_catalog_get_product():
    """Patch catalog-service gRPC client."""
    with patch("src.services.cart_service.get_product") as mock:
        mock.return_value = {
            "product_id": "test-product",
            "name": "Test Product",
            "price": 9.99,
        }
        yield mock


@pytest.fixture
def sample_cart() -> dict[str, Any]:
    return {
        "user_id": "user-1",
        "items": [
            {
                "product_id": "p-1",
                "product_name": "Widget A",
                "unit_price": 10.0,
                "quantity": 2,
            },
        ],
        "total": 20.0,
    }


@pytest.fixture
def user_id() -> str:
    return "user-1"


@pytest.fixture
def product_id() -> str:
    return "test-product"
