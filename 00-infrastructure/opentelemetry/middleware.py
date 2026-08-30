"""FastAPI middleware for OpenTelemetry HTTP tracing.

Provides request/response tracing, error tracking, duration measurement,
and HTTP status code recording.

Usage (in a service's main.py)::

    from opentelemetry.middleware import OTelHTTPMiddleware

    app.add_middleware(OTelHTTPMiddleware, exclude_patterns=["/health"])
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from opentelemetry import trace
from opentelemetry.context import attach, detach, Context
from opentelemetry.propagate import inject, extract
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import Span, SpanKind, Status, StatusCode
from opentelemetry.trace.propagation.w3c import TraceContextTextMapPropagator

from .logs import get_logger, set_correlation_id, get_correlation_id

logger = get_logger("otel-middleware")


class OTelHTTPMiddleware(BaseHTTPMiddleware):
    """FastAPI / Starlette middleware that adds OpenTelemetry tracing.

    Attributes
    ----------
    exclude_patterns:
        URL path prefixes to skip (e.g. ``["/health", "/metrics"]``).
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        exclude_patterns: list[str] | None = None,
        span_name_formatter: Callable[[Request], str] | None = None,
    ) -> None:
        super().__init__(app)
        self.exclude_patterns = exclude_patterns or ["/health", "/ready", "/metrics"]
        self.span_name_formatter = span_name_formatter or self._default_span_name

    @staticmethod
    def _default_span_name(request: Request) -> str:
        """Default span name: ``<METHOD> <path>``."""
        return f"{request.method} {request.url.path}"

    async def dispatch(self, request: Request, call_next) -> Response:
        # ── Skip excluded paths ───────────────────────────────────────
        if any(request.url.path.startswith(p) for p in self.exclude_patterns):
            return await call_next(request)

        # ── Extract trace context from incoming headers ───────────────
        carrier: dict[str, str] = {}
        for key, value in request.headers.items():
            # Normalise header names for OTel propagation
            normalised = key.lower().replace("-", "_")
            carrier[normalised] = value

        ctx = extract(carrier)
        token = attach(ctx)

        # ── Correlation ID ────────────────────────────────────────────
        correlation_id = request.headers.get(
            "x-correlation-id",
            request.headers.get("x-request-id", uuid.uuid4().hex[:16]),
        )
        set_correlation_id(correlation_id)

        # ── Create span ───────────────────────────────────────────────
        tracer = trace.get_tracer("otel-middleware")
        span_name = self.span_name_formatter(request)
        span = tracer.start_span(
            span_name,
            kind=SpanKind.SERVER,
            attributes={
                SpanAttributes.HTTP_METHOD: request.method,
                SpanAttributes.HTTP_URL: str(request.url),
                SpanAttributes.HTTP_SCHEME: request.url.scheme,
                SpanAttributes.NET_PEER_IP: (
                    request.client.host if request.client else ""
                ),
                SpanAttributes.USER_AGENT_ORIGINAL: request.headers.get(
                    "user-agent", ""
                ),
                "http.request.id": correlation_id,
            },
        )

        # ── Inject context into outgoing response headers ─────────────
        response_headers: list[tuple[str, str]] = []
        inject(setter=dict.__setitem__, carrier=dict(response_headers))

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            elapsed = time.perf_counter() - start_time

            # Record response attributes
            span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, response.status_code)
            span.set_status(
                Status(
                    StatusCode.OK
                    if 200 <= response.status_code < 500
                    else StatusCode.ERROR
                )
            )

            # Add trace headers to response
            for key, value in response_headers:
                response.headers[key] = value

            return response

        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            span.record_exception(exc)
            raise

        finally:
            span.set_attribute("http.duration_ms", round(elapsed * 1000, 2))
            span.end()
            detach(token)


# Re-export
__all__ = ["OTelHTTPMiddleware"]
