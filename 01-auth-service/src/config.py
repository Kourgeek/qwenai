"""Application configuration loaded from environment variables via pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralised configuration sourced from ``.env`` / OS environment."""

    # ── gRPC ──────────────────────────────────────────────────────────
    grpc_port: int = 50053
    http_port: int = 8080

    # ── PostgreSQL ────────────────────────────────────────────────────
    db_host: str = "postgres"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "auth_db"

    # ── JWT ───────────────────────────────────────────────────────────
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry: int = 3600        # 1 hour

    # ── Refresh token ────────────────────────────────────────────────
    refresh_token_expiry: int = 86400 * 7  # 7 days

    # ── Redis ─────────────────────────────────────────────────────────
    redis_host: str = "redis"
    redis_port: int = 6379

    # ── Password policy ──────────────────────────────────────────────
    password_min_length: int = 8
    password_require_upper: bool = True
    password_require_lower: bool = True
    password_require_digit: bool = True
    password_require_special: bool = True

    # ── Account lockout ──────────────────────────────────────────────
    account_lockout_enabled: bool = True
    account_lockout_max_attempts: int = 5
    account_lockout_window_seconds: int = 900   # 15 minutes
    account_lockout_duration_seconds: int = 1800  # 30 minutes

    # ── Brute force protection on login ──────────────────────────────
    login_rate_limit_max: int = 10
    login_rate_limit_window: int = 300            # 5 minutes

    # ── Application ───────────────────────────────────────────────────
    app_name: str = "hyperauth-service"
    app_env: str = "development"
    log_level: str = "INFO"

    @property
    def db_url(self) -> str:
        """Return an async SQLAlchemy connection string (asyncpg dialect)."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def redis_url(self) -> str:
        """Return a Redis connection URL."""
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Module-level singleton — call ``get_settings()`` to obtain it.
_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
