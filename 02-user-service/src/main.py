"""FastAPI application + gRPC server lifecycle for the User Service."""

import asyncio
import logging
import sys

from fastapi import FastAPI

from src.config import settings
from src.grpc_server.user_pb2_service import serve

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ── FastAPI app ────────────────────────────────────────────────
app = FastAPI(
    title="User Service",
    description="HyperScale Marketplace — User Service (Phase 4)",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict:
    """Simple health-check endpoint."""
    return {"status": "ok", "service": "user-service"}


# ── gRPC server lifecycle ─────────────────────────────────────
_grpc_server = None


@app.on_event("startup")
async def startup() -> None:
    global _grpc_server
    _grpc_server = await serve(grpc_port=settings.grpc_port)


@app.on_event("shutdown")
async def shutdown() -> None:
    global _grpc_server
    if _grpc_server is not None:
        await _grpc_server.stop(grace=2.0)
        _grpc_server = None


# ── Entry point ───────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.grpc_port,
        log_level=settings.log_level.lower(),
    )
