"""Reusable security middleware for all HyperScale Marketplace services.

Install this package or copy the middleware files into any service
to apply security hardening.

Usage in any FastAPI service:

    from security.middleware import create_security_middleware

    app = FastAPI(...)
    app.add_middleware(create_security_middleware())
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# ── Default security headers ──────────────────────────────────────────

DEFAULT_SECURITY_HEADERS: dict[str, str] = {
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "upgrade-insecure-requests"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=(), payment=(), usb=()",
    "Cache-Control": "no-store, no-cache, must-revalidate, private",
    "Pragma": "no-cache",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds OWASP-recommended security headers to every response."""

    def __init__(
        self,
        app: ASGIApp,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        super().__init__(app)
        self._headers: dict[str, str] = dict(DEFAULT_SECURITY_HEADERS)
        if headers:
            self._headers.update(headers)

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for name, value in self._headers.items():
            if name not in response.headers or response.headers[name] == "":
                response.headers[name] = value
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Generates and propagates a request ID for distributed tracing."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def create_security_middleware(
    headers: Optional[dict[str, str]] = None,
) -> type[SecurityHeadersMiddleware]:
    """Factory to create a security middleware class with custom headers."""
    return type(
        "SecurityHeadersMiddleware",
        (SecurityHeadersMiddleware,),
        {"_headers": dict(DEFAULT_SECURITY_HEADERS) if not headers else headers},
    )


def apply_security_to_app(app, headers: Optional[dict[str, str]] = None) -> None:
    """Convenience function to apply both security and request-id middleware."""
    app.add_middleware(SecurityHeadersMiddleware, headers=headers)
    app.add_middleware(RequestIDMiddleware)
