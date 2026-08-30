"""Security headers middleware for the Auth service.

Applies OWASP-recommended HTTP security headers to every response.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
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


class AuthSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that injects security headers into every response."""

    def __init__(
        self,
        app: ASGIApp,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        super().__init__(app)
        self._headers: dict[str, str] = dict(DEFAULT_HEADERS)
        if headers:
            self._headers.update(headers)

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and attach security headers to response."""
        response = await call_next(request)

        for name, value in self._headers.items():
            if name not in response.headers or response.headers[name] == "":
                response.headers[name] = value

        return response


def add_security_headers(response: Response, headers: Optional[dict[str, str]] = None) -> None:
    """Directly add security headers to a FastAPI ``Response`` object."""
    effective = dict(DEFAULT_HEADERS)
    if headers:
        effective.update(headers)
    for name, value in effective.items():
        if name not in response.headers or response.headers[name] == "":
            response.headers[name] = value
