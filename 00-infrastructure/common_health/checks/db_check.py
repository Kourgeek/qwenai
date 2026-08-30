"""PostgreSQL health check using asyncpg."""

from __future__ import annotations

import logging
from typing import Any

from ..health_check import HealthCheck, HealthCheckResult

logger = logging.getLogger(__name__)


class PostgresHealthCheck(HealthCheck):
    """Check PostgreSQL connectivity by running ``SELECT 1``."""

    def __init__(self, dsn: str, pool_size: int = 5, timeout: float = 5.0) -> None:
        super().__init__(name="postgresql")
        self._dsn = dsn
        self._pool_size = pool_size
        self._timeout = timeout

    async def check(self) -> HealthCheckResult:
        import asyncpg

        conn = None
        try:
            conn = await asyncpg.connect(dsn=self._dsn, timeout=self._timeout)
            await conn.fetchval("SELECT 1")
            server_info = await conn.fetchval("SELECT version()")
            return HealthCheckResult(
                name=self.name,
                status="healthy",
                detail={"version": server_info[:80], "pool_size": self._pool_size},
            )
        except Exception as exc:
            logger.warning("PostgreSQL health check failed: %s", exc)
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                error=str(exc),
            )
        finally:
            if conn is not None:
                await conn.close()
