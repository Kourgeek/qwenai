"""FastAPI application entry-point for the Cart Service."""

from __future__ import annotations

import grpc
import asyncio
import logging
import sys

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.api.cart import router as cart_router
from src.config import settings
from src.grpc_server.cart_pb2_service import CartServiceServicer
from src.grpc_server import cart_pb2_grpc  # type: ignore[attr-defined]
from src.redis_client import cart_redis
from src.services.cart_service import cart_service

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("cart-service")

# ------------------------------------------------------------------
# App factory
# ------------------------------------------------------------------
app = FastAPI(
    title="Cart Service",
    description="HyperScale Marketplace — Cart microservice",
    version="1.0.0",
)

app.include_router(cart_router, prefix="/api/v1")


# ------------------------------------------------------------------
# Health endpoint
# ------------------------------------------------------------------
@app.get("/health", tags=["operations"])
async def health() -> dict:
    return {"status": "ok", "service": "cart-service"}


# ------------------------------------------------------------------
# gRPC server lifecycle
# ------------------------------------------------------------------
grpc_server: grpc.aio.Server | None = None  # type: ignore[name-defined]  # noqa: F821


@app.on_event("startup")
async def startup() -> None:
    """Start Redis connection and gRPC server."""
    await cart_redis.connect()
    global grpc_server  # noqa: PLW0603
    grpc_server = grpc.aio.server()
    cart_pb2_grpc.add_CartServiceServicer_to_server(CartServiceServicer(), grpc_server)
    grpc_server.add_insecure_port(f"[::]:{settings.grpc_port}")
    await grpc_server.start()
    logger.info("gRPC server listening on port %d", settings.grpc_port)


@app.on_event("shutdown")
async def shutdown() -> None:
    """Gracefully stop gRPC server and Redis."""
    if grpc_server is not None:
        await grpc_server.stop(grace=5)
        logger.info("gRPC server stopped")
    await cart_redis.close()
    logger.info("Redis connection closed")
