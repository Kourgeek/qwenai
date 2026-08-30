"""Application configuration — loaded from environment / .env file."""

from __future__ import annotations

from functools import cached_property
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All settings for the Search Service, sourced from env vars or .env."""

    # ── gRPC ───────────────────────────────────────────────────────────────
    grpc_port: int = Field(default=50058, ge=1, le=65535)

    # ── HTTP ───────────────────────────────────────────────────────────────
    http_port: int = Field(default=8083, ge=1, le=65535)

    # ── Elasticsearch ──────────────────────────────────────────────────────
    es_hosts: str = Field(
        default="http://elasticsearch:9200",
        description="Comma-separated list of ES hosts",
    )
    es_index_name: str = Field(default="products")
    es_user: str | None = Field(default=None)
    es_password: str | None = Field(default=None)
    es_cloud_id: str | None = Field(default=None)
    es_api_key: str | None = Field(default=None)
    es_request_timeout: int = Field(default=30, ge=1)
    es_max_retries: int = Field(default=3, ge=0)

    # ── Database (optional audit store) ────────────────────────────────────
    db_host: str = Field(default="postgres")
    db_port: int = Field(default=5432)
    db_name: str = Field(default="marketplace")
    db_user: str = Field(default="postgres")
    db_password: str = Field(default="postgres")
    db_min_size: int = Field(default=2, ge=1)
    db_max_size: int = Field(default=10, ge=1)

    # ── Catalog gRPC service ───────────────────────────────────────────────
    catalog_service_host: str = Field(default="catalog-service")
    catalog_service_port: int = Field(default=50051, ge=1, le=65535)

    # ── Logging ────────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO")

    @property
    def log_level_upper(self) -> str:
        """Return log level normalized to uppercase."""
        return self.log_level.upper()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @cached_property
    def es_hosts_list(self) -> list[str]:
        """Parse the comma-separated ES hosts string into a list."""
        return [h.strip() for h in self.es_hosts.split(",") if h.strip()]

    @cached_property
    def es_http_auth(self) -> tuple[str, str] | None:
        """Return (user, password) if both are set, else None."""
        if self.es_user and self.es_password:
            return (self.es_user, self.es_password)
        return None


# Singleton settings instance — imported by modules that need config
settings = Settings()
