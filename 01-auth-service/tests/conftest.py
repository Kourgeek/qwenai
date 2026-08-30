"""Shared pytest fixtures for async tests."""

from __future__ import annotations

import asyncio
import os
import uuid
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import Settings
from src.database import Base
from src.repositories.auth_repository import AuthRepository
from src.services.auth_service import AuthService
from src.services.password_service import hash_password

# Use an in-memory SQLite database for tests so no external Postgres is needed.
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


# ── Settings override ─────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _override_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force settings to use the test database URL."""
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_NAME", "test_auth_db")
    monkeypatch.setenv("JWT_SECRET", "test-secret-key-at-least-32-chars-long!")
    monkeypatch.setenv("JWT_EXPIRY", "3600")
    monkeypatch.setenv("REDIS_HOST", "localhost")


# ── Async engine & session ────────────────────────────────────────────

@pytest.fixture
async def test_engine():
    """Create an in-memory SQLite engine for tests."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield a fresh async session per test."""
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    session: AsyncSession = factory()
    yield session
    await session.close()


@pytest.fixture
async def repository(test_session: AsyncSession) -> AuthRepository:
    return AuthRepository(test_session)


@pytest.fixture
async def auth_service(repository: AuthRepository) -> AuthService:
    return AuthService(repository)


# ── Helper: create a user in the test DB ──────────────────────────────

@pytest.fixture
async def created_user(
    test_session: AsyncSession,
) -> AsyncGenerator[uuid.UUID, None]:
    """Create a user and return its ID."""
    from src.models.user import User

    user = User(
        email="test@example.com",
        hashed_password=hash_password("TestPass123!"),
        first_name="Test",
        last_name="User",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    yield user.id
    # Cleanup
    await test_session.delete(user)
    await test_session.commit()
