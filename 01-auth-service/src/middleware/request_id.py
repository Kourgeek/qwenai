"""Request ID middleware for the Auth service.

Generates and propagates request IDs for distributed tracing.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import Request, Response

logger = logging.getLogger(__name__)


class RequestIDMiddleware:
    """ASGI middleware that generates a request ID for every request."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        """Generate request ID and attach to request state."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id

        # Wrap send to inject the request ID header
        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                # Update or add x-request-id header
                new_headers = []
                for k, v in headers:
                    if k == b"x-request-id":
                        new_headers.append((b"x-request-id", request_id.encode()))
                    else:
                        new_headers.append((k, v))
                # Ensure header is present
                has_xrid = any(k == b"x-request-id" for k, _ in new_headers)
                if not has_xrid:
                    new_headers.append((b"x-request-id", request_id.encode()))
                message["headers"] = new_headers
            await send(message)

        await self.app(scope, receive, wrapped_send)
