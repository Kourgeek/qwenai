"""Application settings loaded from environment via pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralised configuration backed by .env / OS env vars."""

    # gRPC
    grpc_port: int = 50055

    # PostgreSQL
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "hyperserve_orders"
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_min_size: int = 5
    db_max_size: int = 20

    # Kafka
    kafka_brokers: str = "kafka:9092"
    kafka_order_created_topic: str = "order.created"
    kafka_order_status_changed_topic: str = "order.status_changed"

    # Cart service (gRPC)
    cart_service_host: str = "cart-service"
    cart_service_port: int = 50050

    # Catalog service (gRPC)
    catalog_service_host: str = "catalog-service"
    catalog_service_port: int = 50051

    # Logging
    log_level: str = "INFO"

    model_config = {"env_prefix": ""}  # accept both FOO and prefix-less


settings = Settings()
