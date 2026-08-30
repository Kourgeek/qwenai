"""HyperScale Marketplace — Search Service entry point.

Bootstraps FastAPI, registers routers, and manages gRPC server lifecycle.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import Any

import grpc
import uvicorn
from fastapi import FastAPI

from src.config import settings
from src.grpc_server.search_pb2_grpc import add_SearchServiceServicer_to_server
from src.grpc_server.search_pb2_service import SearchServiceServicer
from src.services.search_service import SearchService

# ── logging setup ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("search-service")


# ── lifespan / lifecycle ─────────────────────────────────────────────────────

_search_service: SearchService | None = None
_grpc_server: grpc.aio.Server | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown of all services."""
    global _search_service, _grpc_server

    # ── startup ────────────────────────────────────────────────────────────
    logger.info("Search Service starting up …")
    _search_service = SearchService()
    await _search_service.connect()

    # Verify ES connectivity
    health = await _search_service.health_check()
    logger.info("Health check: %s", health)

    # Start gRPC server
    _grpc_server = grpc.aio.server()
    servicer = SearchServiceServicer(_search_service)
    add_SearchServiceServicer_to_server(servicer, _grpc_server)
    _grpc_server.add_insecure_port(f"[::]:{settings.grpc_port}")
    await _grpc_server.start()
    logger.info("gRPC server listening on port %s", settings.grpc_port)

    yield

    # ── shutdown ───────────────────────────────────────────────────────────
    logger.info("Search Service shutting down …")
    if _grpc_server:
        await _grpc_server.stop(grace=5)
        _grpc_server = None
    if _search_service:
        await _search_service.close()
        _search_service = None
    logger.info("Search Service stopped.")


# ── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="HyperScale Marketplace — Search Service",
    description="Elasticsearch-backed product search with gRPC and HTTP APIs.",
    version="1.0.0",
    lifespan=lifespan,
)

# Register HTTP routers
from src.api.search import router as search_router  # noqa: E402

app.include_router(search_router)


@app.get("/health", tags=["operations"])
async def health() -> dict[str, Any]:
    """Health check endpoint — returns downstream service status."""
    if _search_service is None:
        return {"status": "unhealthy", "error": "SearchService not initialized"}
    return await _search_service.health_check()


# ── CLI entry-point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.http_port,
        log_level=settings.log_level.lower(),
    )
