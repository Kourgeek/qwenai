"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration for the Cart Service."""

    # gRPC server
    grpc_port: int = 50050

    # HTTP server
    server_port: int = 8081

    # Database (used for audit/persistence layer)
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "cart_service"
    db_user: str = "cart_service"
    db_password: str = ""
    db_min_size: int = 5
    db_max_size: int = 20

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 3
    redis_cart_ttl: int = 86400
    redis_saved_ttl: int = 2592000

    # Auth service gRPC
    auth_service_host: str = "auth-service"
    auth_service_port: int = 50052

    # Catalog service gRPC
    catalog_service_host: str = "catalog-service"
    catalog_service_port: int = 50051

    # Logging
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
