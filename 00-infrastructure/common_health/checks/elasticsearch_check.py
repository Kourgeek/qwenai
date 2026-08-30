"""Elasticsearch health check."""

from __future__ import annotations

import logging

from ..health_check import HealthCheck, HealthCheckResult

logger = logging.getLogger(__name__)


class ElasticsearchHealthCheck(HealthCheck):
    """Check Elasticsearch connectivity via ``ping()``."""

    def __init__(self, es_client: object, timeout: float = 5.0) -> None:
        super().__init__(name="elasticsearch")
        self._client = es_client
        self._timeout = timeout

    async def check(self) -> HealthCheckResult:
        try:
            from elasticsearch import Elasticsearch

            if isinstance(self._client, Elasticsearch):
                # The async client has a ``ping`` coroutine
                if hasattr(self._client, "ping"):
                    is_alive = await self._client.ping()
                else:
                    is_alive = self._client.ping()
            else:
                # Generic: try ping
                is_alive = self._client.ping()

            if is_alive:
                info = await self._client.info() if hasattr(self._client, "info") else {}
                return HealthCheckResult(
                    name=self.name,
                    status="healthy",
                    detail={"version": info.get("version", {}).get("number", "unknown")},
                )
            return HealthCheckResult(name=self.name, status="unhealthy")
        except Exception as exc:
            logger.warning("Elasticsearch health check failed: %s", exc)
            return HealthCheckResult(name=self.name, status="unhealthy", error=str(exc))
