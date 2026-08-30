"""BffService — core business logic for aggregating data from microservices."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as aioredis

from src.config import Settings
from src.grpc_client.auth_client import AuthGrpcClient
from src.grpc_client.user_client import UserGrpcClient
from src.grpc_client.cart_client import CartGrpcClient
from src.grpc_client.order_client import OrderGrpcClient
from src.grpc_client.search_client import SearchGrpcClient
from src.grpc_client.seller_client import SellerGrpcClient
from src.grpc_client.admin_client import AdminGrpcClient
from src.grpc_client.payment_client import PaymentGrpcClient
from src.grpc_client.catalog_client import CatalogHttpClient

logger = logging.getLogger(__name__)


class BffService:
    """Aggregates data from multiple microservices for frontend consumption."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.auth_client = AuthGrpcClient(settings.auth_grpc_target)
        self.user_client = UserGrpcClient(settings.user_grpc_target)
        self.cart_client = CartGrpcClient(settings.cart_grpc_target)
        self.order_client = OrderGrpcClient(settings.order_grpc_target)
        self.search_client = SearchGrpcClient(settings.search_grpc_target)
        self.seller_client = SellerGrpcClient(settings.seller_grpc_target)
        self.admin_client = AdminGrpcClient(settings.admin_grpc_target)
        self.payment_client = PaymentGrpcClient(settings.payment_grpc_target)
        self.catalog_client = CatalogHttpClient(settings.catalog_http_target)

        self._redis: Optional[aioredis.Redis] = None
        self._cache_ttl: int = 300  # 5 minutes default

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Initialize all gRPC channels and Redis connection."""
        await self.auth_client.initialize()
        await self.user_client.initialize()
        await self.cart_client.initialize()
        await self.order_client.initialize()
        await self.search_client.initialize()
        await self.seller_client.initialize()
        await self.admin_client.initialize()
        await self.payment_client.initialize()

        self._redis = aioredis.Redis(
            host=self.settings.redis_host,
            port=self.settings.redis_port,
            decode_responses=True,
            max_connections=20,
        )
        try:
            await self._redis.ping()
            logger.info("Connected to Redis at %s:%d", self.settings.redis_host, self.settings.redis_port)
        except Exception:
            logger.warning("Redis unavailable — caching will be skipped")
            self._redis = None

    async def close(self) -> None:
        """Close all gRPC channels and Redis connection."""
        for client in [
            self.auth_client,
            self.user_client,
            self.cart_client,
            self.order_client,
            self.search_client,
            self.seller_client,
            self.admin_client,
            self.payment_client,
        ]:
            try:
                await client.close()
            except Exception:
                pass
        if self._redis:
            await self._redis.close()

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    async def _get_cache(self, key: str) -> Optional[str]:
        if self._redis is None:
            return None
        try:
            value = await self._redis.get(key)
            return value
        except Exception:
            return None

    async def _set_cache(self, key: str, value: str) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.setex(key, self._cache_ttl, value)
        except Exception:
            pass

    async def _invalidate_cache(self, key: str) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.delete(key)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Public API — aggregation methods
    # ------------------------------------------------------------------

    async def get_user_profile(self, user_id: str) -> dict:
        """Aggregate user profile from user-service.

        Returns:
            Dict with user profile data.
        """
        cache_key = f"bff:profile:{user_id}"
        cached = await self._get_cache(cache_key)
        if cached:
            return self._parse_json(cached)

        try:
            profile = await self.user_client.get_user_profile(user_id)
            await self._set_cache(cache_key, self._to_json(profile))
            return profile
        except Exception as exc:
            logger.error("Failed to get user profile for %s: %s", user_id, exc)
            raise

    async def get_user_cart(self, user_id: str) -> dict:
        """Aggregate user shopping cart from cart-service.

        Returns:
            Dict with cart data.
        """
        cache_key = f"bff:cart:{user_id}"
        cached = await self._get_cache(cache_key)
        if cached:
            return self._parse_json(cached)

        try:
            cart = await self.cart_client.get_cart(user_id)
            await self._set_cache(cache_key, self._to_json(cart))
            return cart
        except Exception as exc:
            logger.error("Failed to get cart for user_id=%s: %s", user_id, exc)
            raise

    async def get_user_orders(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """Aggregate user orders from order-service.

        Returns:
            Dict with orders list and pagination info.
        """
        cache_key = f"bff:orders:{user_id}:{limit}:{offset}"
        cached = await self._get_cache(cache_key)
        if cached:
            return self._parse_json(cached)

        try:
            orders = await self.order_client.get_user_orders(user_id, limit=limit, offset=offset)
            await self._set_cache(cache_key, self._to_json(orders))
            return orders
        except Exception as exc:
            logger.error("Failed to get orders for user_id=%s: %s", user_id, exc)
            raise

    async def search_products(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        category_id: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: str = "relevance",
    ) -> dict:
        """Aggregate product search from search-service.

        Returns:
            Dict with products and pagination info.
        """
        cache_key = f"bff:search:{query}:{limit}:{offset}:{category_id}:{min_price}:{max_price}:{sort_by}"
        cached = await self._get_cache(cache_key)
        if cached:
            return self._parse_json(cached)

        try:
            results = await self.search_client.search_products(
                query=query,
                limit=limit,
                offset=offset,
                category_id=category_id,
                min_price=min_price,
                max_price=max_price,
                sort_by=sort_by,
            )
            await self._set_cache(cache_key, self._to_json(results))
            return results
        except Exception as exc:
            logger.error("Failed to search products for query='%s': %s", query, exc)
            raise

    async def get_seller_info(self, seller_id: str) -> dict:
        """Fetch seller info from seller-service.

        Returns:
            Dict with seller details.
        """
        cache_key = f"bff:seller:{seller_id}"
        cached = await self._get_cache(cache_key)
        if cached:
            return self._parse_json(cached)

        try:
            info = await self.seller_client.get_seller_info(seller_id)
            await self._set_cache(cache_key, self._to_json(info))
            return info
        except Exception as exc:
            logger.error("Failed to get seller info for seller_id=%s: %s", seller_id, exc)
            raise

    # ------------------------------------------------------------------
    # Seller product management
    # ------------------------------------------------------------------

    async def get_seller_products(self, seller_id: str, limit: int = 20, offset: int = 0) -> dict:
        """Fetch products for a seller from catalog-service.

        Returns:
            Dict with products list and pagination.
        """
        cache_key = f"bff:seller:products:{seller_id}:{limit}:{offset}"
        cached = await self._get_cache(cache_key)
        if cached:
            return self._parse_json(cached)

        try:
            import aiohttp
            url = f"{self.settings.catalog_http_target}/products?seller_id={seller_id}&limit={limit}&offset={offset}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        await self._set_cache(cache_key, self._to_json(data))
                        return data
                    elif resp.status == 404:
                        return {"items": [], "total": 0, "skip": offset, "limit": limit}
                    else:
                        body = await resp.text()
                        logger.error("Catalog API error for seller %s: %d - %s", seller_id, resp.status, body)
                        raise Exception(f"Catalog service error: {resp.status}")
        except Exception as exc:
            logger.error("Failed to get seller products for seller_id=%s: %s", seller_id, exc)
            raise

    async def create_seller_product(self, seller_id: str, product_data: dict) -> dict:
        """Create a new product for a seller via catalog-service.

        Args:
            seller_id: UUID of the seller
            product_data: Product data dict (name, slug, price, etc.)

        Returns:
            Created product dict.
        """
        try:
            import aiohttp
            product_data["seller_id"] = seller_id
            url = f"{self.settings.catalog_http_target}/products"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=product_data, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status in (200, 201):
                        return await resp.json()
                    body = await resp.text()
                    logger.error("Catalog create product error: %d - %s", resp.status, body)
                    raise Exception(f"Catalog service error: {resp.status} - {body}")
        except Exception as exc:
            logger.error("Failed to create product for seller %s: %s", seller_id, exc)
            raise

    async def update_seller_product(self, product_id: str, updates: dict) -> dict:
        """Update a product via catalog-service.

        Args:
            product_id: UUID of the product
            updates: Fields to update

        Returns:
            Updated product dict.
        """
        try:
            import aiohttp
            url = f"{self.settings.catalog_http_target}/products/{product_id}"
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, json=updates, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    body = await resp.text()
                    logger.error("Catalog update product error: %d - %s", resp.status, body)
                    raise Exception(f"Catalog service error: {resp.status} - {body}")
        except Exception as exc:
            logger.error("Failed to update product %s: %s", product_id, exc)
            raise

    async def delete_seller_product(self, product_id: str) -> bool:
        """Delete a product via catalog-service.

        Args:
            product_id: UUID of the product

        Returns:
            True if deleted successfully.
        """
        try:
            import aiohttp
            url = f"{self.settings.catalog_http_target}/products/{product_id}"
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    return resp.status == 204
        except Exception as exc:
            logger.error("Failed to delete product %s: %s", product_id, exc)
            raise

    async def get_seller_categories(self, is_active: bool = True) -> dict:
        """Fetch all categories from catalog-service.

        Returns:
            Dict with categories list.
        """
        cache_key = f"bff:categories:{is_active}"
        cached = await self._get_cache(cache_key)
        if cached:
            return self._parse_json(cached)

        try:
            import aiohttp
            url = f"{self.settings.catalog_http_target}/categories?is_active={str(is_active).lower()}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        await self._set_cache(cache_key, self._to_json(data))
                        return data
                    return {"items": []}
        except Exception as exc:
            logger.error("Failed to get categories: %s", exc)
            return {"items": []}

    async def get_seller_stats(self, seller_id: str) -> dict:
        """Fetch seller statistics from seller-service.

        Returns:
            Dict with seller stats (orders, revenue, products count, etc.).
        """
        cache_key = f"bff:seller:stats:{seller_id}"
        cached = await self._get_cache(cache_key)
        if cached:
            return self._parse_json(cached)

        try:
            # Try seller-service gRPC first
            info = await self.seller_client.get_seller_info(seller_id)
            products = await self.get_seller_products(seller_id, limit=1)
            stats = {
                "seller_id": seller_id,
                "business_name": info.get("business_name", ""),
                "total_products": products.get("total", 0),
                "total_orders": 0,
                "total_revenue": 0.0,
                "pending_orders": 0,
                "processing_orders": 0,
                "shipped_orders": 0,
                "delivered_orders": 0,
                "cancelled_orders": 0,
                "rating": info.get("rating", 0),
                "total_ratings": info.get("total_ratings", 0),
                "active_products": 0,
                "low_stock_products": 0,
            }
            await self._set_cache(cache_key, self._to_json(stats))
            return stats
        except Exception as exc:
            logger.error("Failed to get seller stats for seller_id=%s: %s", seller_id, exc)
            return {
                "seller_id": seller_id,
                "total_products": 0,
                "total_orders": 0,
                "total_revenue": 0.0,
            }

    async def get_seller_orders(self, seller_id: str, limit: int = 20, offset: int = 0) -> dict:
        """Fetch orders for a seller from order-service.

        Returns:
            Dict with orders list and pagination.
        """
        cache_key = f"bff:seller:orders:{seller_id}:{limit}:{offset}"
        cached = await self._get_cache(cache_key)
        if cached:
            return self._parse_json(cached)

        try:
            # Try to get orders from order-service
            orders = await self.order_client.get_seller_orders(seller_id, limit=limit, offset=offset)
            await self._set_cache(cache_key, self._to_json(orders))
            return orders
        except AttributeError:
            # order_client may not have get_seller_orders method
            logger.warning("order_client doesn't have get_seller_orders, returning empty")
            return {"items": [], "total": 0, "skip": offset, "limit": limit}
        except Exception as exc:
            logger.error("Failed to get seller orders for seller_id=%s: %s", seller_id, exc)
            return {"items": [], "total": 0, "skip": offset, "limit": limit}

    async def get_dashboard_stats(self) -> dict:
        """Fetch dashboard statistics from admin-service.

        Returns:
            Dict with dashboard metrics.
        """
        cache_key = "bff:dashboard:stats"
        cached = await self._get_cache(cache_key)
        if cached:
            return self._parse_json(cached)

        try:
            stats = await self.admin_client.get_dashboard_stats()
            await self._set_cache(cache_key, self._to_json(stats))
            return stats
        except Exception as exc:
            logger.error("Failed to get dashboard stats: %s", exc)
            raise

    async def get_payment_methods(self, user_id: str) -> dict:
        """Fetch payment methods from payment-service.

        Returns:
            Dict with payment methods list.
        """
        cache_key = f"bff:payments:{user_id}"
        cached = await self._get_cache(cache_key)
        if cached:
            return self._parse_json(cached)

        try:
            methods = await self.payment_client.get_payment_methods(user_id)
            await self._set_cache(cache_key, self._to_json(methods))
            return methods
        except Exception as exc:
            logger.error("Failed to get payment methods for user_id=%s: %s", user_id, exc)
            raise

    # ------------------------------------------------------------------
    # Auth methods (proxy to Auth service via gRPC)
    # ------------------------------------------------------------------

    async def auth_login(self, email: str, password: str) -> dict:
        """Authenticate user via auth service gRPC and return tokens."""
        try:
            result = await self.auth_client.login(email, password)
            return result
        except Exception as exc:
            logger.error("Auth login via gRPC failed: %s", exc)
            raise

    async def auth_register(self, email: str, password: str, first_name: str = "", last_name: str = "") -> dict:
        """Register a new user via auth service gRPC and return tokens."""
        try:
            result = await self.auth_client.register(email, password, first_name, last_name)
            return result
        except Exception as exc:
            logger.error("Auth register via gRPC failed: %s", exc)
            raise

    async def auth_refresh(self, refresh_token: str) -> dict:
        """Refresh access token via auth service gRPC."""
        try:
            result = await self.auth_client.refresh(refresh_token)
            return result
        except Exception as exc:
            logger.error("Auth refresh via gRPC failed: %s", exc)
            raise

    async def auth_logout(self, refresh_token: str) -> None:
        """Logout and invalidate token via auth service gRPC."""
        try:
            await self.auth_client.logout(refresh_token)
        except Exception:
            pass  # Ignore errors on logout

    async def auth_forgot_password(self, email: str) -> dict:
        """Request password reset via auth service."""
        try:
            result = await self.auth_client.forgot_password(email)
            return result
        except Exception:
            return {"email": email, "reset_token": "dummy-reset-token"}

    # ------------------------------------------------------------------
    # Seller methods
    # ------------------------------------------------------------------

    async def seller_register(self, user_id: str, business_name: str = "") -> dict:
        """Register a new seller account."""
        try:
            result = await self.seller_client.register_seller(user_id, business_name)
            return result
        except Exception as exc:
            logger.error("Seller register failed: %s", exc)
            raise

    async def get_seller_products(self, seller_id: str, *, limit: int = 20, offset: int = 0,
                                   status: Optional[str] = None) -> dict:
        """Get products for a seller from catalog service."""
        try:
            result = await self.catalog_client.get_products(seller_id, limit=limit, offset=offset)
            products = result.get("items", [])
            return {
                "products": products,
                "total": result.get("total", len(products)),
                "limit": limit,
                "offset": offset,
            }
        except Exception as exc:
            logger.error("Failed to get seller products for seller_id=%s: %s", seller_id, exc)
            raise

    async def update_seller_product(self, product_id: str, **kwargs) -> dict:
        """Update a product via catalog service."""
        try:
            # Filter out None values
            updates = {k: v for k, v in kwargs.items() if v is not None}
            return await self.catalog_client.update_product(product_id, updates)
        except Exception as exc:
            logger.error("Failed to update seller product: %s", exc)
            raise

    async def delete_seller_product(self, product_id: str) -> None:
        """Delete a product via catalog service."""
        try:
            await self.catalog_client.delete_product(product_id)
        except Exception as exc:
            logger.error("Failed to delete seller product: %s", exc)
            raise

    async def get_seller_stats(self, seller_id: str) -> dict:
        """Get seller statistics from seller service."""
        try:
            stats = await self.seller_client.get_seller_stats(seller_id)
            return stats
        except Exception as exc:
            logger.error("Failed to get seller stats for seller_id=%s: %s", seller_id, exc)
            raise

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_json(obj: dict) -> str:
        import json

        return json.dumps(obj, default=str)

    @staticmethod
    def _parse_json(s: str) -> dict:
        import json

        return json.loads(s)
