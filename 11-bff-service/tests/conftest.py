"""Shared test fixtures for BFF Service."""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def mock_auth_client():
    """Mock auth client."""
    client = AsyncMock()
    client.verify_token = AsyncMock(return_value={"user_id": "test-user-123", "email": "test@example.com"})
    return client


@pytest.fixture
def mock_user_client():
    """Mock user client."""
    client = AsyncMock()
    client.get_user_profile = AsyncMock(return_value={"id": "test-user-123", "first_name": "Test", "last_name": "User"})
    return client


@pytest.fixture
def mock_catalog_client():
    """Mock catalog client."""
    client = AsyncMock()
    client.get_product = AsyncMock(return_value={"id": "prod-1", "name": "Test Product", "price": 99.99})
    client.list_products = AsyncMock(return_value={"products": [], "total": 0})
    return client


@pytest.fixture
def mock_cart_client():
    """Mock cart client."""
    client = AsyncMock()
    client.get_cart = AsyncMock(return_value={"items": []})
    return client


@pytest.fixture
def mock_order_client():
    """Mock order client."""
    client = AsyncMock()
    client.get_user_orders = AsyncMock(return_value={"orders": [], "total": 0})
    client.get_order = AsyncMock(return_value={"id": "order-1", "status": "PENDING"})
    return client


@pytest.fixture
def mock_search_client():
    """Mock search client."""
    client = AsyncMock()
    client.search_products = AsyncMock(return_value={"products": [], "total": 0})
    return client
