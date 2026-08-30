"""Application settings loaded from environment variables via pydantic-settings."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """Central configuration for the Notification Service."""

    # gRPC
    grpc_port: int = Field(default=50057, env="GRPC_PORT")

    # HTTP
    http_port: int = Field(default=8086, env="HTTP_PORT")

    # Kafka
    kafka_brokers: str = Field(default="kafka:9092", env="KAFKA_BROKERS")
    kafka_order_topic: str = Field(default="order.created", env="KAFKA_ORDER_TOPIC")
    kafka_payment_topic: str = Field(default="payment.completed", env="KAFKA_PAYMENT_TOPIC")
    kafka_refund_topic: str = Field(default="payment.refunded", env="KAFKA_REFUND_TOPIC")

    # Redis
    redis_host: str = Field(default="redis", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")

    # Mail (SMTP)
    mail_host: str = Field(default="mailhog", env="MAIL_HOST")
    mail_port: int = Field(default=1025, env="MAIL_PORT")
    mail_user: str = Field(default="noreply@marketplace.local", env="MAIL_USER")
    mail_password: str = Field(default="", env="MAIL_PASSWORD")

    # Logging
    log_level: str = Field(default="info", env="LOG_LEVEL")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Singleton settings instance
settings = Settings()
