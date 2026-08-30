"""Application configuration — loaded from environment via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All settings for the User Service."""

    # gRPC / HTTP
    grpc_port: int = 50053

    # PostgreSQL
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "user_service"
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_echo: bool = False

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 2

    # Auth service (gRPC)
    auth_service_host: str = "auth-service"
    auth_service_port: int = 50052

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
