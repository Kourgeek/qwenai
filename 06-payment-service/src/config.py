"""
Application settings — loaded from environment via pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed settings backed by environment variables and .env file."""

    # -- Database -----------------------------------------------------------
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "hypercale_payment"
    db_user: str = "payment_user"
    db_password: str = "change_me_in_production"
    db_pool_size: int = 20
    db_max_overflow: int = 10

    # -- Redis --------------------------------------------------------------
    redis_url: str = "redis://redis:6379/0"

    # -- Stripe -------------------------------------------------------------
    stripe_secret_key: str = "sk_test_placeholder"
    stripe_webhook_secret: str = "whsec_placeholder"
    stripe_webhook_url: str = "https://api.marketplace.example.com/api/v1/webhook/stripe"

    # -- YooMoney -----------------------------------------------------------
    yoomoney_shop_id: str = ""
    yoomoney_token: str = ""
    yoomoney_confirmation_url: str = "https://api.marketplace.example.com/api/v1/webhook/yoomoney"

    # -- Kafka --------------------------------------------------------------
    kafka_brokers: str = "kafka:9092"
    kafka_topic: str = "marketplace-events"

    # -- gRPC ---------------------------------------------------------------
    grpc_port: int = 50056

    # -- Application --------------------------------------------------------
    log_level: str = "INFO"
    app_env: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
