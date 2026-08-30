"""HTTP service health check using httpx."""

from __future__ import annotations

import logging

from ..health_check import HealthCheck, HealthCheckResult

logger = logging.getLogger(__name__)


class HttpHealthCheck(HealthCheck):
    """Check an HTTP service by hitting its ``/health`` endpoint."""

    def __init__(
        self,
        url: str,
        method: str = "GET",
        expected_status: int = 200,
        timeout: float = 5.0,
    ) -> None:
        super().__init__(name=url)
        self._url = url
        self._method = method
        self._expected_status = expected_status
        self._timeout = timeout

    async def check(self) -> HealthCheckResult:
        import httpx

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.request(self._method, self._url)
                if response.status_code == self._expected_status:
                    return HealthCheckResult(
                        name=self.name,
                        status="healthy",
                        detail={"status_code": response.status_code, "headers": dict(response.headers)},
                    )
                return HealthCheckResult(
                    name=self.name,
                    status="unhealthy",
                    detail={"status_code": response.status_code},
                )
            except httpx.TimeoutException as exc:
                logger.warning("HTTP health check timeout for %s: %s", self._url, exc)
                return HealthCheckResult(name=self.name, status="unhealthy", error=f"timeout: {exc}")
            except Exception as exc:
                logger.warning("HTTP health check failed for %s: %s", self._url, exc)
                return HealthCheckResult(name=self.name, status="unhealthy", error=str(exc))
