"""FastAPI application entry-point for Gateway service with hardening."""

import logging
import sys
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings
from src.grpc_client.auth_client import AuthGrpcClient
from src.middleware.auth import AuthMiddleware, get_auth_middleware
from src.middleware.cors import CORSMiddleware
from src.middleware.logging import LoggingMiddleware
from src.middleware.rate_limiter import RateLimiter, InMemoryStore, RedisStore
from src.api.gateway import router as gateway_router

# ------------------------------------------------------------------
# Import security modules
# ------------------------------------------------------------------
from src.security.headers import SecurityHeadersMiddleware, add_security_headers
from src.security.rate_limiter import get_client_ip

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("gateway-service")

# ------------------------------------------------------------------
# Application
# ------------------------------------------------------------------

app = FastAPI(
    title="Gateway Service",
    description="API Gateway for HyperScale Marketplace",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(gateway_router, prefix="")

# ------------------------------------------------------------------
# Shared dependencies
# ------------------------------------------------------------------

_auth_client: AuthGrpcClient | None = None
_rate_limiter: RateLimiter | None = None


# ------------------------------------------------------------------
# Lifespan — startup / shutdown
# ------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize gRPC client, Redis, and rate limiter."""
    global _auth_client, _rate_limiter

    # gRPC auth client
    _auth_client = AuthGrpcClient(settings.auth_grpc_target)
    await _auth_client.initialize()

    # Rate limiter — try Redis first, fall back to in-memory
    try:
        import redis.asyncio as aioredis
        redis_client = aioredis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True,
            max_connections=20,
        )
        await redis_client.ping()
        logger.info("Connected to Redis at %s:%d", settings.redis_host, settings.redis_port)

        _rate_limiter = RateLimiter(
            store=RedisStore(redis_client),
            max_requests=settings.rate_limit_max_requests,
            window_seconds=settings.rate_limit_window_seconds,
        )
    except Exception as exc:
        logger.warning("Redis unavailable (%s) — using in-memory rate limiter", exc)
        _rate_limiter = RateLimiter(
            store=InMemoryStore(),
            max_requests=settings.rate_limit_max_requests,
            window_seconds=settings.rate_limit_window_seconds,
        )

    logger.info("Gateway started on port %d", settings.server_port)
    yield

    # Shutdown
    if _auth_client:
        await _auth_client.close()
    logger.info("Gateway shut down")


app.router.lifespan_context = lambda app: lifespan(app)


# ------------------------------------------------------------------
# Middleware registration
# ------------------------------------------------------------------

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Generate and propagate a request ID for tracing."""
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Apply security headers to every response."""
    response = await call_next(request)

    add_security_headers(response)

    # HSTS
    hsts_value = f"max-age={settings.hsts_max_age}"
    if settings.hsts_include_subdomains:
        hsts_value += "; includeSubDomains"
    if settings.hsts_preload:
        hsts_value += "; preload"
    response.headers["Strict-Transport-Security"] = hsts_value

    # CSP
    csp_parts = [
        f"default-src {settings.csp_default_src}",
        f"script-src {settings.csp_script_src}",
        f"style-src {settings.csp_style_src}",
        f"img-src {settings.csp_img_src}",
        f"font-src {settings.csp_font_src}",
        f"connect-src {settings.csp_connect_src}",
        f"frame-ancestors {settings.csp_frame_ancestors}",
        f"base-uri {settings.csp_base_uri}",
        f"form-action {settings.csp_form_action}",
    ]
    if settings.csp_upgrade_insecure:
        csp_parts.append("upgrade-insecure-requests")
    response.headers["Content-Security-Policy"] = "; ".join(csp_parts)

    # Permissions-Policy
    response.headers["Permissions-Policy"] = (
        "geolocation=(), camera=(), microphone=(), payment=(), usb=()"
    )

    return response


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Authenticate requests via gRPC Auth service."""
    # Skip auth for public endpoints
    public_paths = [
        "/health", "/docs", "/redoc", "/openapi.json",
        "/api/auth/login", "/api/auth/register", "/api/auth/refresh", "/api/auth/logout",
        "/static/", "/favicon.ico",
    ]
    for path in public_paths:
        if request.url.path.startswith(path):
            return await call_next(request)

    if _auth_client is None:
        return await call_next(request)

    middleware_instance = get_auth_middleware(_auth_client)
    from fastapi.security import HTTPBearer
    security = HTTPBearer(auto_error=False)
    credentials = await security(request)
    await middleware_instance(request, credentials)
    response = await call_next(request)
    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests."""
    if _rate_limiter is None:
        return await call_next(request)

    # Check IP-based rate limit
    client_ip = await get_client_ip(request)
    if client_ip != "unknown":
        await _rate_limiter.check(request)

    response = await call_next(request)
    return response


@app.middleware("http")
async def admin_ip_check_middleware(request: Request, call_next):
    """Restrict admin endpoints to whitelisted IPs."""
    path = request.url.path
    if path.startswith("/admin") or path.startswith("/internal"):
        client_ip = await get_client_ip(request)
        if client_ip != "unknown" and client_ip not in settings.admin_ip_whitelist_set:
            return JSONResponse(
                status_code=403,
                content={"detail": "Forbidden: IP not in whitelist"},
            )

    response = await call_next(request)
    return response


@app.middleware("http")
async def request_size_limit_middleware(request: Request, call_next):
    """Reject requests with body larger than the configured limit."""
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            size = int(content_length)
            if size > settings.max_request_body_size:
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": f"Request body too large. "
                                  f"Max allowed: {settings.max_request_body_size} bytes.",
                    },
                )
        except ValueError:
            pass

    response = await call_next(request)
    return response


@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """Apply request timeout for forwarded requests."""
    from fastapi import HTTPException
    import asyncio

    try:
        response = await asyncio.wait_for(
            call_next(request),
            timeout=settings.request_timeout,
        )
        return response
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Gateway timeout — request exceeded the configured timeout.",
        )


# ------------------------------------------------------------------
# Error handlers
# ------------------------------------------------------------------

@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
