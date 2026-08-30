"""Shared test fixtures for Order Service."""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_cart_client():
    """Return a mock for ``src.grpc_client.cart_client.get_cart``."""
    mock = AsyncMock(return_value={"items": [], "total": 0.0, "currency": "USD"})
    return mock


@pytest.fixture
def mock_catalog_client():
    """Return a mock for ``src.grpc_client.catalog_client.get_product``."""
    mock = AsyncMock(
        return_value={
            "id": 1,
            "name": "Test Product",
            "price": 29.99,
            "sku": "SKU-TEST",
            "image_url": "https://example.com/test.jpg",
        }
    )
    return mock


@pytest.fixture
def mock_kafka_publisher():
    """Return a mock for ``OrderKafkaPublisher``."""
    mock = AsyncMock()
    mock.publish_order_created = AsyncMock()
    mock.publish_order_status_changed = AsyncMock()
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_session():
    """Return a MagicMock acting as an ``AsyncSession``."""
    session = MagicMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.get = AsyncMock()
    session.close = AsyncMock()
    return session
