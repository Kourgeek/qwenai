"""Shared test fixtures for Gateway Service."""
import asyncio

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
    """Mock auth client for gateway tests."""
    from unittest.mock import AsyncMock
    client = AsyncMock()
    client.verify_token = AsyncMock(return_value={"user_id": "test-user-123", "email": "test@example.com"})
    return client


@pytest.fixture
def mock_bff_client():
    """Mock BFF client for gateway tests."""
    from unittest.mock import AsyncMock
    client = AsyncMock()
    client.get_profile = AsyncMock(return_value={"id": "test-user-123", "name": "Test User"})
    return client
