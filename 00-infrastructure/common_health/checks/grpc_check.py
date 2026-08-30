"""gRPC service health check."""

from __future__ import annotations

import logging

from ..health_check import HealthCheck, HealthCheckResult

logger = logging.getLogger(__name__)


class GrpcHealthCheck(HealthCheck):
    """Check a gRPC service by attempting a channel connection."""

    def __init__(self, target: str, timeout: float = 5.0) -> None:
        super().__init__(name="grpc")
        self._target = target
        self._timeout = timeout

    async def check(self) -> HealthCheckResult:
        import grpc

        channel = grpc.aio.insecure_channel(self._target)
        try:
            # Try to connect; this will raise if the target is unreachable
            await grpc.aio.channel(channel).channel().ready().result(timeout=self._timeout)
            return HealthCheckResult(
                name=self.name,
                status="healthy",
                detail={"target": self._target},
            )
        except Exception as exc:
            logger.warning("gRPC health check failed for %s: %s", self._target, exc)
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                error=str(exc),
            )
        finally:
            await channel.close()
