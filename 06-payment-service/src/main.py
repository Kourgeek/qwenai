"""
HyperScale Payment Service — FastAPI application entry point.

Exposes:
  - HTTP health endpoint
  - HTTP webhook routes
  - gRPC server (lifespan startup/shutdown)
"""

import asyncio
import logging
import sys

from fastapi import FastAPI
from grpc import ssl_server_credentials
from uvicorn import Config, Server

from src.api import webhook
from src.config import settings
from src.grpc_server.payment_pb2_service import PaymentServiceServicer
from src.grpc_server import payment_pb2_grpc

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="HyperScale Payment Service",
    description="Phase 7 — Payment processing with Stripe & YooMoney",
    version="0.1.0",
)

# Register webhook routes
app.include_router(webhook.router)


@app.get("/health")
async def health() -> dict:
    """Kubernetes / Docker health check."""
    return {"status": "ok", "service": "payment-service"}


# ---------------------------------------------------------------------------
# gRPC server lifecycle
# ---------------------------------------------------------------------------

_grpc_server = None


async def _start_grpc_server() -> None:
    """Start the gRPC server on GRPC_PORT."""
    global _grpc_server
    from concurrent import futures

    _grpc_server = _create_server()
    payment_pb2_grpc.add_PaymentServiceServicer_to_server(
        PaymentServiceServicer(),
        _grpc_server,
    )
    _grpc_server.start()
    logger.info("gRPC server started on port %s", settings.grpc_port)


def _create_server():
    """Create a gRPC server (TLS if certs available, otherwise plaintext)."""
    from concurrent import futures
    from grpc import server

    grpc_server = server(
        futures.ThreadPoolExecutor(max_workers=20),
    )
    creds = _server_credentials()
    if creds:
        grpc_server.add_secure_port(f"[::]:{settings.grpc_port}", creds)
    else:
        grpc_server.add_insecure_port(f"[::]:{settings.grpc_port}")
    return grpc_server


def _server_credentials():
    """Return TLS credentials if certs exist, else None (plaintext)."""
    import os

    cert_path = os.environ.get("TLS_CERT_PATH")
    key_path = os.environ.get("TLS_KEY_PATH")
    ca_path = os.environ.get("TLS_CA_PATH")

    if cert_path and key_path:
        try:
            with open(cert_path, "rb") as f:
                cert = f.read()
            with open(key_path, "rb") as f:
                key = f.read()
            ca = open(ca_path, "rb").read() if ca_path else None
            return ssl_server_credentials([(key, cert)] + ([ca] if ca else []))
        except FileNotFoundError:
            logger.warning("TLS certs not found — running gRPC in plaintext")
    return None


async def _stop_grpc_server() -> None:
    global _grpc_server
    if _grpc_server:
        _grpc_server.stop(grace=5)
        logger.info("gRPC server stopped")


@app.on_event("startup")
async def startup_event() -> None:
    await _start_grpc_server()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await _stop_grpc_server()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=50056,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower(),
    )
