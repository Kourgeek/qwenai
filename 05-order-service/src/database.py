"""Async SQLAlchemy engine and session-factory setup."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings

engine = create_async_engine(
    url=(
        f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    ),
    echo=False,
    pool_size=settings.db_min_size,
    max_overflow=settings.db_max_size,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session and ensure proper close."""
    session: AsyncSession = async_session_factory()
    try:
        yield session
    finally:
        await session.close()
