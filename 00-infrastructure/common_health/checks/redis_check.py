"""Redis health check."""

from __future__ import annotations

import logging

from ..health_check import HealthCheck, HealthCheckResult

logger = logging.getLogger(__name__)


class RedisHealthCheck(HealthCheck):
    """Check Redis connectivity via ``PING``."""

    def __init__(self, redis_client: object, timeout: float = 5.0) -> None:
        """
        Parameters
        ----------
        redis_client:
            An ``redis.asyncio.Redis`` instance (or ``redis.Redis`` for sync).
        timeout:
            Maximum seconds to wait for a response.
        """
        super().__init__(name="redis")
        self._client = redis_client
        self._timeout = timeout

    async def check(self) -> HealthCheckResult:
        try:
            import redis

            if hasattr(self._client, "ping"):
                # asyncredis
                result = await self._client.ping()
            else:
                result = self._client.ping()
            info = await self._client.info("server") if hasattr(self._client, "info") else {}
            return HealthCheckResult(
                name=self.name,
                status="healthy" if result else "unhealthy",
                detail={"redis_version": info.get("redis_version", "unknown")},
            )
        except redis.ConnectionError as exc:
            logger.warning("Redis health check failed: %s", exc)
            return HealthCheckResult(name=self.name, status="unhealthy", error=str(exc))
        except Exception as exc:
            logger.warning("Redis health check error: %s", exc)
            return HealthCheckResult(name=self.name, status="unhealthy", error=str(exc))
