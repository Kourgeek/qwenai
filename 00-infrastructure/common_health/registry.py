"""Registry that aggregates multiple ``HealthCheck`` instances."""

from __future__ import annotations

import logging
from typing import Any

from .health_check import HealthCheck, HealthCheckResult

logger = logging.getLogger(__name__)


class HealthCheckRegistry:
    """Manages a collection of ``HealthCheck`` objects.

    Usage
    -----
    .. code-block:: python

        registry = HealthCheckRegistry()
        registry.add_check("postgresql", PostgresHealthCheck(db_url))
        registry.add_check("redis", RedisHealthCheck(redis_client))

        # Get overall health
        overall = await registry.get_health()

        # Get per-dependency details
        detailed = await registry.get_detailed_health()
    """

    def __init__(self, service_name: str = "unknown-service") -> None:
        self._service_name = service_name
        self._checks: dict[str, HealthCheck] = {}

    def add_check(self, name: str, check: HealthCheck) -> None:
        """Register a health check under *name*."""
        self._checks[name] = check
        logger.info("Registered health check: %s", name)

    def remove_check(self, name: str) -> None:
        """Unregister a health check by *name*."""
        self._checks.pop(name, None)

    def get_check_names(self) -> list[str]:
        return list(self._checks.keys())

    async def get_health(self) -> str:
        """Return ``"healthy"`` only if **all** registered checks pass."""
        if not self._checks:
            return "healthy"

        for check in self._checks.values():
            result = await check.check_with_timing()
            if not result.is_healthy():
                return "unhealthy"
        return "healthy"

    async def get_checks_status(self) -> dict[str, str]:
        """Return ``{name: status}`` for every registered check."""
        status: dict[str, str] = {}
        for name, check in self._checks.items():
            result = await check.check_with_timing()
            status[name] = result.status
        return status

    async def get_detailed_health(self) -> dict[str, Any]:
        """Return full health report with per-dependency details."""
        import datetime

        dependencies = []
        all_healthy = True

        for name, check in self._checks.items():
            result = await check.check_with_timing()
            if not result.is_healthy():
                all_healthy = False
            dependencies.append(result.to_dict())

        overall = "healthy" if all_healthy else "unhealthy"

        return {
            "status": overall,
            "service": self._service_name,
            "dependencies": dependencies,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        }

    async def is_ready(self) -> bool:
        """Convenience: ``True`` when the overall health is ``"healthy"``."""
        return await self.get_health() == "healthy"
