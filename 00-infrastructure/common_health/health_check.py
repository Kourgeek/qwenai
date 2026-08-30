"""Base classes for the health-check framework.

Exports
-------
HealthCheck
HealthCheckResult
HealthCheckRegistry
CompositeHealthCheck
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

# ── Result of a single health check ───────────────────────────────────


class HealthCheckResult:
    """Immutable snapshot of one dependency health check."""

    __slots__ = ("name", "status", "response_time_ms", "detail", "error")

    def __init__(
        self,
        name: str,
        status: str,
        response_time_ms: float | None = None,
        detail: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        self.name = name
        self.status = status  # "healthy" | "unhealthy" | "unknown"
        self.response_time_ms = response_time_ms
        self.detail = detail or {}
        self.error = error

    def is_healthy(self) -> bool:
        return self.status == "healthy"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "response_time_ms": self.response_time_ms,
            "detail": self.detail,
        }


# ── Abstract base check ────────────────────────────────────────────────


class HealthCheck(ABC):
    """Base class for all dependency health checks.

    Subclasses must implement ``check()`` which returns a
    ``HealthCheckResult``.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    async def check(self) -> HealthCheckResult:
        """Run the health check and return the result."""
        ...

    async def check_with_timing(self) -> HealthCheckResult:
        """Run *check* and record wall-clock response time."""
        start = time.monotonic()
        try:
            result = await self.check()
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                response_time_ms=round(elapsed_ms, 2),
                error=str(exc),
            )
        elapsed_ms = (time.monotonic() - start) * 1000
        result.response_time_ms = round(elapsed_ms, 2)
        return result
