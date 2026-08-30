"""Refined CORS middleware for the API Gateway.

Supports configurable allowed origins, methods, headers, credentials,
and max-age. Rejects requests from disallowed origins entirely
(instead of passing through without headers).
"""

import logging
from typing import Optional, Set

from fastapi import Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Defaults
# ------------------------------------------------------------------

DEFAULT_ALLOWED_ORIGINS: Set[str] = {
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
}

DEFAULT_ALLOWED_METHODS: Set[str] = {
    "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS",
}

DEFAULT_ALLOWED_HEADERS: Set[str] = {
    "authorization", "content-type", "x-requested-with",
    "x-csrf-token", "x-api-key", "accept", "origin",
}

DEFAULT_EXPOSE_HEADERS: Set[str] = {
    "x-rate-limit-limit", "x-rate-limit-remaining",
    "x-rate-limit-reset", "x-correlation-id", "x-request-id",
}

DEFAULT_MAX_AGE: int = 86400  # 24 hours


class CORSMiddleware:
    """ASGI-compatible CORS middleware with strict origin validation.

    Unlike the permissive default, this middleware **rejects** cross-origin
    requests whose origin is not in the allowlist.

    Parameters
    ----------
    app :
        The next ASGI application in the chain.
    allowed_origins :
        Set of allowed frontend origins. Empty set disables CORS entirely.
    allowed_methods :
        HTTP methods permitted for cross-origin requests.
    allowed_headers :
        Request headers that may be sent cross-origin.
    expose_headers :
        Response headers the browser may expose to JavaScript.
    allow_credentials :
        Whether to include cookies / auth headers in cross-origin requests.
    max_age :
        Seconds the browser caches the preflight response.
    """

    def __init__(
        self,
        app,
        *,
        allowed_origins: Optional[Set[str]] = None,
        allowed_methods: Optional[Set[str]] = None,
        allowed_headers: Optional[Set[str]] = None,
        expose_headers: Optional[Set[str]] = None,
        allow_credentials: bool = True,
        max_age: int = DEFAULT_MAX_AGE,
    ) -> None:
        self.app = app
        self.allowed_origins = allowed_origins or DEFAULT_ALLOWED_ORIGINS
        self.allowed_methods = allowed_methods or DEFAULT_ALLOWED_METHODS
        self.allowed_headers = allowed_headers or DEFAULT_ALLOWED_HEADERS
        self.expose_headers = expose_headers or DEFAULT_EXPOSE_HEADERS
        self.allow_credentials = allow_credentials
        self.max_age = max_age

    async def __call__(self, scope, receive, send) -> None:
        """Handle CORS for each request."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        origin = request.headers.get("origin", "")

        # No origin header → not a CORS request
        if not origin:
            await self.app(scope, receive, send)
            return

        # Reject disallowed origins entirely
        if origin not in self.allowed_origins:
            logger.warning("CORS rejected: origin '%s' not in allowlist", origin)
            response = Response(status_code=403, headers={
                "access-control-allow-origin": origin,
                "vary": "Origin",
            })
            await response(scope, receive, send)
            return

        # Preflight (OPTIONS) request
        if request.method == "OPTIONS":
            headers = self._build_cors_headers(origin)
            response = Response(status_code=204, headers=headers)
            await response(scope, receive, send)
            return

        # Normal request — pass through with CORS headers
        await self._add_cors_headers_and_forward(request, origin, scope, receive, send)

    def _build_cors_headers(self, origin: str) -> dict[str, str]:
        """Build CORS response headers for a given origin."""
        headers: dict[str, str] = {}
        headers["access-control-allow-origin"] = origin
        headers["access-control-allow-methods"] = ", ".join(sorted(self.allowed_methods))
        headers["access-control-allow-headers"] = ", ".join(sorted(self.allowed_headers))
        headers["access-control-expose-headers"] = ", ".join(sorted(self.expose_headers))
        headers["access-control-max-age"] = str(self.max_age)
        if self.allow_credentials:
            headers["access-control-allow-credentials"] = "true"
        headers["vary"] = "Origin"
        return headers

    async def _add_cors_headers_and_forward(
        self,
        request: Request,
        origin: str,
        scope: dict,
        receive,
        send,
    ) -> None:
        """Forward the request and inject CORS headers into the response."""
        cors_headers = self._build_cors_headers(origin)

        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                resp_headers = dict(message.get("headers", []))
                for name, value in cors_headers.items():
                    resp_headers.append((name.encode(), value.encode()))
                message["headers"] = resp_headers
            await send(message)

        await self.app(scope, receive, wrapped_send)
