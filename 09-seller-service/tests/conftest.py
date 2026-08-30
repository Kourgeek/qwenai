"""Pytest configuration and shared fixtures for Seller Service tests."""

import asyncio
import uuid
from typing import AsyncGenerator

import pytest
from pytest import FixtureRequest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.database import async_session_factory
from src.grpc_client import auth_client, catalog_client, order_client
from src.repositories import seller_repository
from src.repositories import seller_product_repository
from src.services.seller_service import SellerService


# ------------------------------------------------------------------
# Event-loop scope
# ------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop() -> AsyncGenerator[asyncio.AbstractEventLoop, None]:
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ------------------------------------------------------------------
# Test database (in-memory SQLite for speed)
# ------------------------------------------------------------------

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(TEST_DB_URL, echo=False)
_test_session_factory = async_sessionmaker(bind=_test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
async def _create_test_tables() -> AsyncGenerator[None, None]:
    """Create all tables once per test session."""
    from src.models.seller import Base
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a fresh transactional session per test."""
    async with _test_session_factory() as session:
        yield session


# ------------------------------------------------------------------
# Mock gRPC clients
# ------------------------------------------------------------------

@pytest.fixture
def mock_auth_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch auth_client.verify_token to always return True."""
    async def _verify(token: str) -> bool:
        return True
    monkeypatch.setattr(auth_client, "verify_token", _verify)


@pytest.fixture
def mock_catalog_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch catalog_client methods."""
    async def _get_product(product_id: str) -> dict:
        return {"id": product_id, "name": "Test Product", "status": "APPROVED"}

    async def _list_by_seller(seller_id: str) -> list[dict]:
        return [
            {"id": str(uuid.uuid4()), "seller_id": seller_id, "name": "Product A", "status": "APPROVED"},
            {"id": str(uuid.uuid4()), "seller_id": seller_id, "name": "Product B", "status": "APPROVED"},
        ]

    monkeypatch.setattr(catalog_client, "get_product", _get_product)
    monkeypatch.setattr(catalog_client, "list_products_by_seller", _list_by_seller)


@pytest.fixture
def mock_order_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch order_client.get_seller_orders."""
    async def _get_orders(seller_id: str, page: int = 1, page_size: int = 20) -> dict:
        return {"orders": [], "total": 0, "page": page, "page_size": page_size}

    monkeypatch.setattr(order_client, "get_seller_orders", _get_orders)


# ------------------------------------------------------------------
# Service instance
# ------------------------------------------------------------------

@pytest.fixture
def seller_service(
    mock_auth_client,
    mock_catalog_client,
    mock_order_client,
) -> SellerService:
    """Return a SellerService with all external clients mocked."""
    return SellerService()


# ------------------------------------------------------------------
# Helper: create a seller record directly in the test DB
# ------------------------------------------------------------------

@pytest.fixture
async def test_seller(db_session: AsyncSession) -> uuid.UUID:
    """Create and return a seller record for use in tests."""
    uid = uuid.uuid4()
    seller = await seller_repository.create_seller(
        session=db_session,
        user_id=uid,
        company_name="Test Corp",
        inn="123456789012",
        status="APPROVED",
    )
    await db_session.commit()
    return seller.id
