"""HyperScale Marketplace - Seller Service (Phase 10).

FastAPI entry-point with gRPC server lifecycle management.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from grpc import aio
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

import uvicorn

from src.config import settings
from src.database import engine
from src.grpc_server import seller_pb2
from src.grpc_server import seller_pb2_grpc
from src.grpc_server.seller_pb2_service import SellerServiceServicer

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# gRPC server
# ------------------------------------------------------------------

_grpc_server: aio.Server | None = None


async def _start_grpc_server() -> None:
    """Start the gRPC server on GRPC_PORT."""
    global _grpc_server
    _grpc_server = aio.server()
    seller_pb2_grpc.add_SellerServiceServicer_to_server(
        SellerServiceServicer(), _grpc_server
    )
    _grpc_server.add_insecure_port(f"0.0.0.0:{settings.grpc_port}")
    await _grpc_server.start()
    logger.info("gRPC server started on port %s", settings.grpc_port)


async def _stop_grpc_server() -> None:
    """Gracefully shutdown the gRPC server."""
    global _grpc_server
    if _grpc_server:
        await _grpc_server.stop(grace=5)
        logger.info("gRPC server stopped")


# ------------------------------------------------------------------
# FastAPI lifespan
# ------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown of gRPC + DB resources."""
    await _start_grpc_server()
    yield
    await _stop_grpc_server()
    # Dispose engine
    await engine.dispose()


# ------------------------------------------------------------------
# Application factory
# ------------------------------------------------------------------

app = FastAPI(
    title="Seller Service",
    description="HyperScale Marketplace - Seller Management (Phase 10)",
    version="1.0.0",
    lifespan=lifespan,
)

# Register routers
from src.api import sellers  # noqa: E402

app.include_router(sellers.router)


@app.get("/health", tags=["operations"])
async def health():
    """Health-check endpoint."""
    return {
        "status": "healthy",
        "service": "seller-service",
        "grpc_port": settings.grpc_port,
        "http_port": settings.http_port,
    }


# ------------------------------------------------------------------
# CLI entry-point
# ------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.http_port,
        reload=False,
    )
