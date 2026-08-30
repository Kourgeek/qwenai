"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration sourced from environment variables and .env file."""

    # Server
    server_port: int = 8080
    grpc_port: int = 50051

    # PostgreSQL
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "catalog_db"
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_min_pool_size: int = 5
    db_max_pool_size: int = 20

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_max_connections: int = 20

    # Logging
    log_level: str = "info"

    model_config = {"env_prefix": "", "case_sensitive": True}

    @property
    def database_url(self) -> str:
        """Build asyncpg-compatible SQLAlchemy database URL."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def redis_url(self) -> str:
        """Build Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()
