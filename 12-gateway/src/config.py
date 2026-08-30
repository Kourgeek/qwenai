"""Gateway service configuration using pydantic-settings."""

import os
from typing import Optional, Set

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Server ──────────────────────────────────────────────────────
    server_port: int = 8080
    server_host: str = "0.0.0.0"

    # ── Auth service (gRPC) ────────────────────────────────────────
    auth_service_host: str = "auth-service"
    auth_service_port: int = 50054

    # ── BFF service (HTTP) ────────────────────────────────────────
    bff_service_host: str = "bff-service"
    bff_service_port: int = 8085

    # ── Logging ────────────────────────────────────────────────────
    log_level: str = "info"

    # ── Request size limit (bytes) ─────────────────────────────────
    max_request_body_size: int = 10 * 1024 * 1024  # 10 MB default

    # ── Request timeout (seconds) ──────────────────────────────────
    request_timeout: int = 30

    # ── IP whitelist for admin endpoints ───────────────────────────
    admin_ip_whitelist: str = os.getenv(
        "ADMIN_IP_WHITELIST", "127.0.0.1,::1"
    )

    # ── CORS settings ──────────────────────────────────────────────
    cors_allowed_origins: str = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8080",
    )
    cors_allowed_methods: str = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    cors_allowed_headers: str = (
        "authorization,content-type,x-requested-with,x-csrf-token,"
        "x-api-key,accept,origin"
    )
    cors_max_age: int = 86400  # 24 hours
    cors_allow_credentials: bool = True

    # ── Rate limiting defaults ─────────────────────────────────────
    rate_limit_max_requests: int = 100
    rate_limit_window_seconds: int = 60

    # ── Redis ──────────────────────────────────────────────────────
    redis_host: str = "redis"
    redis_port: int = 6379

    # ── Security headers ───────────────────────────────────────────
    hsts_max_age: int = 63072000  # 2 years
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True

    # ── Content-Security-Policy ────────────────────────────────────
    csp_default_src: str = "'self'"
    csp_script_src: str = "'self'"
    csp_style_src: str = "'self' 'unsafe-inline'"
    csp_img_src: str = "'self' data: https:"
    csp_font_src: str = "'self'"
    csp_connect_src: str = "'self'"
    csp_frame_ancestors: str = "'none'"
    csp_base_uri: str = "'self'"
    csp_form_action: str = "'self'"
    csp_upgrade_insecure: bool = True

    model_config = {"env_file": None, "env_file_encoding": "utf-8"}

    @property
    def auth_grpc_target(self) -> str:
        return f"{self.auth_service_host}:{self.auth_service_port}"

    @property
    def bff_service_url(self) -> str:
        return f"http://{self.bff_service_host}:{self.bff_service_port}"

    @property
    def parsed_cors_origins(self) -> Set[str]:
        return {o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()}

    @property
    def parsed_cors_methods(self) -> Set[str]:
        return {m.strip() for m in self.cors_allowed_methods.split(",") if m.strip()}

    @property
    def parsed_cors_headers(self) -> Set[str]:
        return {h.strip() for h in self.cors_allowed_headers.split(",") if h.strip()}

    @property
    def admin_ip_whitelist_set(self) -> Set[str]:
        return {ip.strip() for ip in self.admin_ip_whitelist.split(",") if ip.strip()}


settings = Settings()
