"""Async database engine and session factories."""

from collections.abc import AsyncGenerator

from asyncpg import Connection
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings

DATABASE_URL = (
    f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}"
    f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
)

async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=settings.db_min_pool_size,
    max_overflow=settings.db_max_pool_size,
    pool_pre_ping=True,
)


@event.listens_for(async_engine.sync_engine, "connect")
def _set_connection_isolation(connection: Connection, _) -> None:
    """Set READ COMMITTED isolation for every new connection."""
    from sqlalchemy.dialects import postgresql

    dialect = postgresql.dialect()
    cursor = connection.cursor()
    cursor.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
    cursor.close()


async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a scoped async session for dependency injection."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
