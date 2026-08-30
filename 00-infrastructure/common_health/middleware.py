"""Health-check middleware for FastAPI.

This middleware is optional — services can call the registry directly from
``/health``, ``/health/ready``, ``/health/live`` route handlers instead.
It is provided for convenience when you want a generic ``/health`` that
auto-delegates to the registry.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .registry import HealthCheckRegistry

logger = logging.getLogger(__name__)


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Adds ``/health`` endpoint that delegates to a ``HealthCheckRegistry``.

    The middleware intercepts ``GET /health`` and returns the aggregated
    health status.  All other paths pass through unchanged.

    Parameters
    ----------
    app:
        The parent ASGI / FastAPI application.
    registry:
        A ``HealthCheckRegistry`` instance that holds all dependency checks.
    """

    def __init__(self, app, registry: HealthCheckRegistry) -> None:  # type: ignore[valid-type]
        super().__init__(app)
        self._registry = registry

    async def dispatch(self, request: Request, call_next) -> Response:
        # Only intercept GET /health
        if request.method == "GET" and request.url.path == "/health":
            return await self._handle_health(request)
        return await call_next(request)

    async def _handle_health(self, request: Request) -> JSONResponse:
        detailed = await self._registry.get_detailed_health()
        return JSONResponse(status_code=200, content=detailed)
