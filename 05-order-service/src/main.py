"""FastAPI application + gRPC lifecycle management."""

from __future__ import annotations

import asyncio
import logging
import sys

from fastapi import FastAPI
from grpc import aio

from src.config import settings
from src.grpc_server.order_pb2_service import OrderServicer
from src.kafka.publisher import OrderKafkaPublisher
from src.models.order import Base

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ── FastAPI ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Order Service",
    description="HyperScale Marketplace — Order domain service (Phase 6)",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "order-service"}


# ── gRPC server ──────────────────────────────────────────────────────────

grpc_server: aio.Server | None = None
kafka_publisher: OrderKafkaPublisher | None = None


@app.on_event("startup")
async def startup() -> None:
    global grpc_server, kafka_publisher

    kafka_publisher = OrderKafkaPublisher(broker=settings.kafka_brokers)

    # Register servicer (stubbed proto — wire after codegen)
    order_servicer = OrderServicer(kafka_publisher=kafka_publisher)

    # Placeholder: bind the real proto service
    # from src.proto import order_pb2_grpc
    # order_pb2_grpc.add_OrderServiceServicer_to_server(order_servicer, grpc_server)

    grpc_server = aio.server()
    grpc_server.add_insecure_port(f"[::]:{settings.grpc_port}")
    await grpc_server.start()
    logger.info("gRPC server listening on port %s", settings.grpc_port)


@app.on_event("shutdown")
async def shutdown() -> None:
    global grpc_server

    if grpc_server:
        await grpc_server.stop(grace=5)
        logger.info("gRPC server stopped")

    if kafka_publisher:
        await kafka_publisher.close()


# ── entry-point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.grpc_port,
        reload=False,
    )
