"""Shared test fixtures for the Admin Service test suite."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings
from src.database import async_session_factory
from src.models.admin import AdminUser, AuditLog
from src.repositories.admin_repository import AdminRepository
from src.repositories.audit_repository import AuditRepository
from src.services.admin_service import AdminService


# ---------------------------------------------------------------------------
# In-memory SQLite engine for tests (avoids needing a real Postgres)
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
_test_session_factory = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)


async def _create_test_db() -> None:
    """Create tables in the test database."""
    from src.models.admin import Base  # noqa: F401
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="session", autouse=True)
def event_loop() -> asyncio.AbstractEventLoop:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


# ---------------------------------------------------------------------------
# Database session fixture
# ---------------------------------------------------------------------------

@pytest.fixture
async def db_session() -> AsyncSession:
    """Provide a fresh database session per test."""
    session = _test_session_factory()
    yield session
    await session.close()


# ---------------------------------------------------------------------------
# Mock gRPC clients
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_auth_client(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = MagicMock()
    mock.verify_token = AsyncMock(return_value=True)
    mock.get_user_roles = AsyncMock(return_value=["user-001"])
    monkeypatch.setattr("src.services.admin_service.auth_client", mock)
    return mock


@pytest.fixture
def mock_catalog_client(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = MagicMock()
    mock.get_product = AsyncMock(return_value={"id": "p-1", "status": "PENDING"})
    mock.list_products = AsyncMock(return_value=[
        {"id": "p-1", "status": "PENDING"},
        {"id": "p-2", "status": "APPROVED"},
    ])
    monkeypatch.setattr("src.services.admin_service.catalog_client", mock)
    return mock


@pytest.fixture
def mock_order_client(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = MagicMock()
    mock.get_order = AsyncMock(return_value={"id": "o-1", "status": "PENDING"})
    mock.list_orders = AsyncMock(return_value=[
        {"id": "o-1", "status": "PENDING"},
        {"id": "o-2", "status": "COMPLETED"},
    ])
    monkeypatch.setattr("src.services.admin_service.order_client", mock)
    return mock


@pytest.fixture
def mock_seller_client(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = MagicMock()
    mock.get_seller = AsyncMock(return_value={"id": "s-1", "status": "PENDING"})
    mock.list_sellers = AsyncMock(return_value=[
        {"id": "s-1", "status": "PENDING"},
        {"id": "s-2", "status": "ACTIVE"},
    ])
    monkeypatch.setattr("src.services.admin_service.seller_client", mock)
    return mock


# ---------------------------------------------------------------------------
# AdminService fixture
# ---------------------------------------------------------------------------

@pytest.fixture
async def admin_service(
    db_session: AsyncSession,
    mock_auth_client: MagicMock,
    mock_catalog_client: MagicMock,
    mock_order_client: MagicMock,
    mock_seller_client: MagicMock,
) -> AdminService:
    """Build an ``AdminService`` backed by the test DB and mock clients."""
    admin_repo = AdminRepository(db_session)
    audit_repo = AuditRepository(db_session)
    return AdminService(admin_repo, audit_repo)


# ---------------------------------------------------------------------------
# AdminUser factory helper
# ---------------------------------------------------------------------------

@pytest.fixture
async def test_admin_user(db_session: AsyncSession) -> AdminUser:
    """Create a test admin user."""
    admin = AdminUser(
        user_id="user-001",
        role="SUPER_ADMIN",
        permissions=["admin:*"],
    )
    db_session.add(admin)
    await db_session.flush()
    await db_session.refresh(admin)
    return admin


# ---------------------------------------------------------------------------
# HTTP test client
# ---------------------------------------------------------------------------

@pytest.fixture
async def client(
    admin_service: AdminService,
    db_session: AsyncSession,
) -> AsyncClient:
    """HTTP test client with the admin router mounted."""
    from src.api.admin import router as admin_router
    from fastapi import FastAPI

    inner_app = FastAPI()
    inner_app.include_router(admin_router)

    # Override the dependency to use our pre-built service
    async def _get_service():
        return admin_service

    inner_app.dependency_overrides[admin_router.dependencies[0]] = _get_service

    transport = ASGITransport(app=inner_app)
    return AsyncClient(transport=transport, base_url="http://test")
