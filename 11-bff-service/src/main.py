"""FastAPI application entry-point for BFF Service."""

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.bff import router as bff_router, auth_router, set_bff_service
from src.config import settings
from src.services.bff_service import BffService

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("bff-service")

# ------------------------------------------------------------------
# Application
# ------------------------------------------------------------------

app = FastAPI(
    title="BFF Service",
    description="Backend-for-Frontend service for HyperScale Marketplace",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware — allows frontend on port 3000 to call BFF on port 8089
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

app.include_router(bff_router, prefix="")
app.include_router(auth_router)

# ------------------------------------------------------------------
# Health check
# ------------------------------------------------------------------


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "bff-service", "version": "1.0.0"}


# ------------------------------------------------------------------
# Lifespan — startup / shutdown
# ------------------------------------------------------------------

_bff_service: BffService = None  # type: ignore[assignment]


@app.on_event("startup")
async def startup():
    """Initialize BFF service and gRPC clients."""
    global _bff_service
    _bff_service = BffService(settings)
    await _bff_service.initialize()
    set_bff_service(_bff_service)
    logger.info("BFF service started on port %d", settings.server_port)


@app.on_event("shutdown")
async def shutdown():
    """Close all connections."""
    if _bff_service:
        await _bff_service.close()
    logger.info("BFF service shut down")


# ------------------------------------------------------------------
# Error handlers
# ------------------------------------------------------------------


@app.exception_handler(Exception)
async def unhandled_error_handler(request, exc):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
