"""HyperScale Marketplace — Catalog Service (Phase 3).

FastAPI application with gRPC server for managing categories, brands,
tags, and products.
"""

import asyncio
import logging
import sys

import uvicorn
from fastapi import FastAPI
from grpc import server as grpc_server
from grpc_reflection.v1alpha import reflection

from src.config import settings
from src.grpc_server.catalog_pb2_service import CatalogServiceServicer
from src.grpc_server import catalog_pb2_grpc as catalog_pb2_grpc
from src.api import categories, brands, tags, products

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("catalog-service")

# Create FastAPI application
app = FastAPI(
    title="HyperScale Catalog Service",
    description="Phase 3: gRPC + REST API for categories, brands, tags, and products",
    version="0.1.0",
)

# Register routers
app.include_router(categories.router, prefix="/api/v1")
app.include_router(brands.router, prefix="/api/v1")
app.include_router(tags.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestrators."""
    return {"status": "ok", "service": "catalog-service"}


def _create_grpc_server() -> grpc_server:
    """Create and configure the gRPC server with reflection enabled."""
    services = (
        catalog_pb2_grpc.add_CatalogServiceServicer_to_server,
    )
    servicer = CatalogServiceServicer()
    grpc_srv = grpc_server(
        [
            ("grpc.max_send_message_length", 50 * 1024 * 1024),
            ("grpc.max_receive_message_length", 50 * 1024 * 1024),
        ]
    )
    services[0](servicer, grpc_srv)
    # Enable reflection for gRPC-Web and debugging
    service_names = (
        catalog_pb2_grpc.CatalogServiceServicer.__name__,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(service_names, grpc_srv)
    return grpc_srv


# Start gRPC server in the background
grpc_srv = _create_grpc_server()


@app.on_event("startup")
async def startup_grpc():
    """Start the gRPC server on application startup."""
    grpc_srv.add_insecure_port(f"[::]:{settings.grpc_port}")
    grpc_srv.start()
    logger.info("gRPC server started on port %d", settings.grpc_port)


@app.on_event("shutdown")
async def shutdown_grpc():
    """Gracefully stop the gRPC server."""
    grpc_srv.stop(grace=5)
    logger.info("gRPC server stopped")


@app.on_event("startup")
async def startup_http():
    """Log HTTP server startup."""
    logger.info("HTTP server will start on port %d", settings.server_port)


async def main():
    """Run both HTTP and gRPC servers concurrently."""
    config = uvicorn.Config(
        "src.main:app",
        host="0.0.0.0",
        port=settings.server_port,
        log_level=settings.log_level,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.server_port,
        log_level=settings.log_level,
    )
