"""Application settings loaded from environment / .env file."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Database ---
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "hyper_admin"
    db_user: str = "admin"
    db_password: str = "changeme_admin_db"
    db_min_pool_size: int = 5
    db_max_pool_size: int = 20

    # --- Redis ---
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 10
    redis_password: str | None = None

    # --- Auth Service (gRPC) ---
    auth_service_host: str = "auth-service"
    auth_service_port: int = 50052

    # --- Catalog Service (gRPC) ---
    catalog_service_host: str = "catalog-service"
    catalog_service_port: int = 50051

    # --- Order Service (gRPC) ---
    order_service_host: str = "order-service"
    order_service_port: int = 50055

    # --- Seller Service (gRPC) ---
    seller_service_host: str = "seller-service"
    seller_service_port: int = 9090

    # --- Ports ---
    grpc_port: int = 50053
    http_port: int = 8085

    # --- Logging ---
    log_level: str = "info"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
