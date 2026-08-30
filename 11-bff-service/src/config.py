"""BFF Service configuration using pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    server_port: int = 8085

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379

    # gRPC services
    auth_service_host: str = "auth-service"
    auth_service_port: int = 50054

    user_service_host: str = "user-service"
    user_service_port: int = 50053

    catalog_service_host: str = "catalog-service"
    catalog_service_port: int = 50051

    cart_service_host: str = "cart-service"
    cart_service_port: int = 50050

    order_service_host: str = "order-service"
    order_service_port: int = 50055

    payment_service_host: str = "payment-service"
    payment_service_port: int = 50056

    search_service_host: str = "search-service"
    search_service_port: int = 50058

    seller_service_host: str = "seller-service"
    seller_service_port: int = 9090

    admin_service_host: str = "admin-service"
    admin_service_port: int = 8085

    # Logging
    log_level: str = "info"

    model_config = {"env_file": None, "env_file_encoding": "utf-8"}

    @property
    def auth_grpc_target(self) -> str:
        return f"{self.auth_service_host}:{self.auth_service_port}"

    @property
    def user_grpc_target(self) -> str:
        return f"{self.user_service_host}:{self.user_service_port}"

    @property
    def catalog_grpc_target(self) -> str:
        return f"{self.catalog_service_host}:{self.catalog_service_port}"

    @property
    def catalog_http_target(self) -> str:
        return f"http://{self.catalog_service_host}:8080/api/v1"

    @property
    def seller_http_target(self) -> str:
        return f"http://{self.seller_service_host}:8085"

    @property
    def cart_grpc_target(self) -> str:
        return f"{self.cart_service_host}:{self.cart_service_port}"

    @property
    def order_grpc_target(self) -> str:
        return f"{self.order_service_host}:{self.order_service_port}"

    @property
    def payment_grpc_target(self) -> str:
        return f"{self.payment_service_host}:{self.payment_service_port}"

    @property
    def search_grpc_target(self) -> str:
        return f"{self.search_service_host}:{self.search_service_port}"

    @property
    def seller_grpc_target(self) -> str:
        return f"{self.seller_service_host}:{self.seller_service_port}"

    @property
    def admin_grpc_target(self) -> str:
        return f"{self.admin_service_host}:{self.admin_service_port}"


settings = Settings()
