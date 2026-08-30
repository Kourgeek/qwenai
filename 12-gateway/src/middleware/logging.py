"""Request/response logging middleware for the API Gateway.

Logs every incoming HTTP request with method, path, client IP,
correlation ID, and outgoing response with status code, duration,
and response size.
"""

import asyncio
import logging
import time
import uuid
from typing import Optional

from fastapi import Request, Response

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """ASGI middleware that logs request/response lifecycle.

    Attributes:
        app: The next ASGI application in the chain.
        log_request_body: Whether to log request body content (sensitive data).
        log_response_body: Whether to log response body content (sensitive data).
        max_body_log_length: Maximum bytes of body to log.
    """

    def __init__(
        self,
        app,
        *,
        log_request_body: bool = False,
        log_response_body: bool = False,
        max_body_log_length: int = 512,
    ) -> None:
        self.app = app
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_log_length = max_body_log_length

    async def __call__(self, scope, receive, send) -> None:
        """Log request and response for each HTTP call."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        start_time = time.perf_counter()

        # Generate correlation ID if not present
        correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Capture request details
        method = request.method
        path = request.url.path
        query_string = request.url.query
        client_host = request.client.host if request.client else "unknown"
        content_length = request.headers.get("content-length", "0")

        # Log request
        self._log_request(
            method=method,
            path=path,
            query_string=query_string,
            client_ip=client_host,
            correlation_id=correlation_id,
            headers=dict(request.headers),
            content_length=int(content_length),
        )

        # Capture request body if enabled
        request_body: Optional[str] = None
        if self.log_request_body:
            body_bytes = await self._get_body(receive)
            if body_bytes:
                request_body = body_bytes[: self.max_body_log_length].decode("utf-8", errors="replace")

        # Wrap send to capture response
        response_started = {"headers": {}}

        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                response_started["status"] = message.get("status", 0)
                response_started["headers"] = {
                    k.decode(): v.decode() for k, v in message.get("headers", [])
                }
            elif message["type"] == "http.response.body":
                body_bytes = message.get("body", b"")
                response_started["body_length"] = len(body_bytes)
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Request %s %s correlation_id=%s duration_ms=%.2f status=500 error=%s",
                method,
                path,
                correlation_id,
                duration_ms,
                exc,
                exc_info=True,
            )
            raise

        # Log response
        status_code = response_started.get("status", 0)
        body_length = response_started.get("body_length", 0)
        duration_ms = (time.perf_counter() - start_time) * 1000

        self._log_response(
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            body_length=body_length,
            correlation_id=correlation_id,
            response_headers=response_started.get("headers", {}),
            response_body=response_started.get("response_body"),
        )

    @staticmethod
    async def _get_body(receive) -> bytes:
        """Read the request body from the ASGI receive channel."""
        body_parts = []
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                break
            if message.get("body"):
                body_parts.append(message["body"])
            if message.get("more_body") is False:
                break
        return b"".join(body_parts)

    @staticmethod
    def _log_request(
        method: str,
        path: str,
        query_string: str,
        client_ip: str,
        correlation_id: str,
        headers: dict,
        content_length: int,
    ) -> None:
        """Log incoming request details."""
        logger.info(
            "INBOUND  method=%-7s path=%-40s query=%s client_ip=%s correlation_id=%s content_length=%d headers=%s",
            method,
            path,
            query_string[:200] if query_string else "",
            client_ip,
            correlation_id,
            content_length,
            {k: v for k, v in headers.items() if k.lower() not in ("authorization", "cookie", "x-api-key")},
        )

    @staticmethod
    def _log_response(
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        body_length: int,
        correlation_id: str,
        response_headers: dict,
        response_body: Optional[str] = None,
    ) -> None:
        """Log outgoing response details."""
        log = logger.info if status_code < 400 else logger.warning if status_code < 500 else logger.error
        log(
            "OUTBOUND  method=%-7s path=%-40s status=%d duration_ms=%.2f body_bytes=%d correlation_id=%s",
            method,
            path,
            status_code,
            duration_ms,
            body_length,
            correlation_id,
        )

        if response_body and response_body.strip():
            snippet = response_body[:256].replace("\n", " ")
            log("RESPONSE_BODY  snippet=%s", snippet)
