"""Security-headers middleware for HyperScale Marketplace.

Applies OWASP-recommended HTTP security headers to every response.
Designed to be imported and mounted as a FastAPI middleware or
used as a response hook in any service.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Default header values (OWASP recommendations)
# ------------------------------------------------------------------

DEFAULT_HEADERS: dict[str, str] = {
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
    """ASGI middleware that injects security headers into every response.

    Parameters
    ----------
    app : ASGIApp
        The next ASGI application in the chain.
    headers : dict[str, str], optional
        Custom header overrides. Defaults to OWASP-recommended values.
    """

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
            # Don't override headers already explicitly set by the endpoint
            if name not in response.headers or response.headers[name] == "":
                response.headers[name] = value

        return response


# ------------------------------------------------------------------
# Convenience function for services that don't use BaseHTTPMiddleware
# ------------------------------------------------------------------

def add_security_headers(response: Response, headers: Optional[dict[str, str]] = None) -> None:
    """Directly add security headers to a FastAPI ``Response`` object.

    Useful for response middleware or ``@app.middleware("http")`` hooks.
    """
    effective = dict(DEFAULT_HEADERS)
    if headers:
        effective.update(headers)
    for name, value in effective.items():
        if name not in response.headers or response.headers[name] == "":
            response.headers[name] = value


# ------------------------------------------------------------------
# Per-environment presets
# ------------------------------------------------------------------

def development_headers() -> dict[str, str]:
    """Headers suitable for local development (more permissive CSP)."""
    return {
        "Content-Security-Policy": (
            "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' http://localhost:* ws://localhost:*; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "upgrade-insecure-requests"
        ),
        **{k: v for k, v in DEFAULT_HEADERS.items() if k != "Content-Security-Policy"},
    }


def production_headers() -> dict[str, str]:
    """Headers for production (strictest settings)."""
    return dict(DEFAULT_HEADERS)


def staging_headers() -> dict[str, str]:
    """Headers for staging (slightly relaxed for debugging)."""
    h = dict(DEFAULT_HEADERS)
    # Allow CSP report-uri for monitoring (no enforcement)
    h["Content-Security-Policy"] = (
        h["Content-Security-Policy"]
        + "; report-uri https://csp-report.example.com/csp"
    )
    return h
