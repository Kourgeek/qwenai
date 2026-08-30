"""FastAPI application entry-point for the Admin Service."""

import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.config import settings
from src.api.admin import router as admin_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# gRPC server management
# ---------------------------------------------------------------------------

_grpc_server: uvicorn.Server | None = None


async def _start_grpc_server() -> None:
    """Start the gRPC server in the background."""
    global _grpc_server
    # Placeholder: wire the real AdminServiceServicer once the proto
    # stubs are generated.
    #
    # from src.grpc_server.admin_pb2_service import AdminServiceServicer
    # from src.services.admin_service import AdminService
    # from src.repositories.admin_repository import AdminRepository
    # from src.repositories.audit_repository import AuditRepository
    # from src.database import async_session_factory
    #
    # async with async_session_factory() as session:
    #     admin_repo = AdminRepository(session)
    #     audit_repo = AuditRepository(session)
    #     admin_svc = AdminService(admin_repo, audit_repo)
    #     servicer = AdminServiceServicer(admin_svc)
    #
    # _grpc_server = grpc.aio.server()
    # AdminServiceServicer.bindservicer(_grpc_server, servicer)
    # _grpc_server.add_insecure_port(f"[::]:{settings.grpc_port}")
    # await _grpc_server.start()
    # logger.info("gRPC server listening on port %s", settings.grpc_port)
    pass


async def _stop_grpc_server() -> None:
    """Gracefully shut down the gRPC server."""
    global _grpc_server
    if _grpc_server is not None:
        await _grpc_server.stop(grace=2)
        _grpc_server = None
        logger.info("gRPC server stopped")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: start/stop gRPC server."""
    logger.info("Admin Service starting up")
    await _start_grpc_server()
    yield
    logger.info("Admin Service shutting down")
    await _stop_grpc_server()


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="HyperScale Marketplace — Admin Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(admin_router, prefix="")


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Health-check endpoint for load balancers and orchestrators."""
    return {"status": "ok", "service": "admin"}
