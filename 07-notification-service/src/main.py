"""FastAPI application entry-point for the Notification Service."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.config import settings
from src.kafka.consumer import OrderKafkaConsumer
from src.api.notifications import router as notifications_router
from src.grpc_server.notification_pb2_service import grpc_manager

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Kafka consumer
# ------------------------------------------------------------------
kafka_consumer = OrderKafkaConsumer()

# ------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the full lifecycle of the Notification Service."""
    # -- Startup --
    logger.info("Starting Notification Service (HTTP port=%d, gRPC port=%d)",
                settings.http_port, settings.grpc_port)

    # Start Kafka consumer
    kafka_consumer.setup()
    kafka_consumer.start(asyncio.get_event_loop())
    logger.info("Kafka consumer started")

    # Start gRPC server
    await grpc_manager.start(settings.grpc_port)
    logger.info("gRPC server started on port %d", settings.grpc_port)

    yield

    # -- Shutdown --
    logger.info("Shutting down Notification Service")
    await grpc_manager.stop(grace=5)
    await kafka_consumer.stop()
    logger.info("Shutdown complete")


# ------------------------------------------------------------------
# Application factory
# ------------------------------------------------------------------
app = FastAPI(
    title="HyperScale Notification Service",
    version="1.0.0",
    lifespan=lifespan,
)

# Register routers
app.include_router(notifications_router)


# ------------------------------------------------------------------
# Health endpoint
# ------------------------------------------------------------------
@app.get("/health", tags=["health"])
async def health() -> JSONResponse:
    """Health-check endpoint for load balancer / orchestrator probes."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "notification-service",
            "version": "1.0.0",
        },
    )


# ------------------------------------------------------------------
# CLI entry-point
# ------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.http_port,
        log_level=settings.log_level,
    )
