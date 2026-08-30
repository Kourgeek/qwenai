"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized configuration for Seller Service."""

    # gRPC server
    grpc_port: int = 9090

    # HTTP server
    http_port: int = 8085

    # PostgreSQL
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "hypermarket_seller"
    db_user: str = "seller_service"
    db_password: str = "seller_service_secret"
    db_pool_size: int = 20
    db_max_overflow: int = 10

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 9
    redis_password: str = ""

    # Auth service (gRPC)
    auth_service_host: str = "auth-service"
    auth_service_port: int = 50052

    # Catalog service (gRPC)
    catalog_service_host: str = "catalog-service"
    catalog_service_port: int = 50051

    # Order service (gRPC)
    order_service_host: str = "order-service"
    order_service_port: int = 50055

    # Logging
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
