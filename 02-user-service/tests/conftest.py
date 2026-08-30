"""Shared test fixtures for the User Service test suite."""

import asyncio
import os
import sys
import uuid
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure the project root is on sys.path so ``src`` imports work.
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ── Patch settings before any service code imports ─────────────
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "user_service_test")
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_PASSWORD", "postgres")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "2")
os.environ.setdefault("AUTH_SERVICE_HOST", "auth-service")
os.environ.setdefault("AUTH_SERVICE_PORT", "50052")
os.environ.setdefault("GRPC_PORT", "50053")
os.environ.setdefault("LOG_LEVEL", "DEBUG")


# ── In-memory SQLite for tests (no external DB needed) ─────────
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop shared across the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
async def db_engine():
    """Create an in-memory SQLite async engine for tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    # Import here so Base is available
    from src.database import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a fresh DB session per test."""
    factory = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)
    session: AsyncSession = factory()
    yield session
    await session.close()


@pytest.fixture()
async def user_id():
    """Return a deterministic test UUID."""
    return uuid.uuid4()


@pytest.fixture()
async def address_id():
    return uuid.uuid4()


@pytest.fixture()
async def product_id():
    return str(uuid.uuid4())


# ── Mock auth client ──────────────────────────────────────────
@pytest.fixture()
def mock_auth_client(monkeypatch):
    """Replace auth_client.get_user_from_token with an async mock."""
    mock = AsyncMock(return_value={
        "user_id": str(uuid.uuid4()),
        "email": "test@example.com",
        "username": "testuser",
    })
    import src.grpc_client.auth_client as auth_client_mod

    monkeypatch.setattr(auth_client_mod, "get_user_from_token", mock)
    monkeypatch.setattr(auth_client_mod, "verify_token", AsyncMock(return_value=(True, "ok")))
    return mock


# ── Helper: insert a user directly into the test DB ───────────
@pytest.fixture()
async def inserted_user(db_session, user_id):
    """Create and return a User row in the test DB."""
    from src.models.user import User

    user = User(
        id=user_id,
        email="test@example.com",
        username="testuser",
        display_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
