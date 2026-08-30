"""gRPC client for Seller service.

Handles seller info queries via Seller service gRPC interface.
"""

import grpc
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SellerGrpcClient:
    """Client for Seller service gRPC communication."""

    def __init__(self, target: str):
        self.target = target
        self._channel: Optional[grpc.aio.Channel] = None

    async def initialize(self) -> None:
        """Initialize the gRPC channel."""
        self._channel = grpc.aio.insecure_channel(
            self.target,
            options=[
                ("grpc.max_metadata_size", 65536),
                ("grpc.keepalive_time_ms", 10000),
                ("grpc.keepalive_timeout_ms", 5000),
            ],
        )

    async def close(self) -> None:
        """Close the gRPC channel."""
        if self._channel:
            await self._channel.close()
            self._channel = None

    async def get_seller_info(self, seller_id: str) -> dict:
        """Fetch seller information by seller ID.

        Args:
            seller_id: The unique seller identifier.

        Returns:
            Dict with seller details.

        Raises:
            grpc.aio.AioRpcError: If gRPC call fails.
        """
        if not self._channel:
            raise grpc.aio.AioRpcError(code=grpc.StatusCode.UNAVAILABLE)

        from src.grpc_client._seller_pb2 import GetSellerRequest
        from src.grpc_client._seller_pb2_grpc import SellerStub

        stub = SellerStub(self._channel)
        try:
            response = await stub.GetSeller(
                GetSellerRequest(seller_id=seller_id),
                timeout=5.0,
            )
            return {
                "seller_id": response.seller_id,
                "business_name": response.business_name,
                "contact_email": response.contact_email,
                "rating": response.rating,
                "total_sales": response.total_sales,
                "joined_at": response.joined_at,
                "is_verified": response.is_verified,
                "address": {
                    "street": response.address.street,
                    "city": response.address.city,
                    "state": response.address.state,
                    "country": response.address.country,
                    "postal_code": response.address.postal_code,
                },
            }
        except grpc.aio.AioRpcError as exc:
            logger.error("Seller gRPC call failed for seller_id=%s: %s", seller_id, exc)
            raise

    async def register_seller(self, user_id: str, business_name: str = "") -> dict:
        """Register a new seller account."""
        if not self._channel:
            raise grpc.aio.AioRpcError(code=grpc.StatusCode.UNAVAILABLE)

        from src.grpc_client._seller_pb2 import RegisterSellerRequest
        from src.grpc_client._seller_pb2_grpc import SellerStub

        stub = SellerStub(self._channel)
        try:
            response = await stub.RegisterSeller(
                RegisterSellerRequest(user_id=user_id, business_name=business_name),
                timeout=5.0,
            )
            return {
                "seller_id": response.seller_id,
                "user_id": response.user_id,
                "business_name": response.business_name,
                "status": response.status,
                "commission_rate": response.commission_rate,
            }
        except grpc.aio.AioRpcError as exc:
            logger.error("Seller register gRPC call failed for user_id=%s: %s", user_id, exc)
            raise

    async def get_seller_products(self, seller_id: str, *, limit: int = 20, offset: int = 0) -> list:
        """Get products for a seller from catalog service."""
        if not self._channel:
            raise grpc.aio.AioRpcError(code=grpc.StatusCode.UNAVAILABLE)

        from src.grpc_client._seller_pb2 import GetSellerProductsRequest
        from src.grpc_client._seller_pb2_grpc import SellerStub

        stub = SellerStub(self._channel)
        try:
            response = await stub.GetSellerProducts(
                GetSellerProductsRequest(seller_id=seller_id, limit=limit, offset=offset),
                timeout=5.0,
            )
            return [
                {
                    "id": p.id,
                    "name": p.name,
                    "slug": p.slug,
                    "description": p.description,
                    "sku": p.sku,
                    "category_id": p.category_id,
                    "brand_id": p.brand_id,
                    "seller_id": p.seller_id,
                    "status": p.status,
                    "price": p.price,
                    "compare_at_price": p.compare_at_price,
                    "cost_price": p.cost_price,
                    "quantity": p.quantity,
                    "is_active": p.is_active,
                    "is_featured": p.is_featured,
                    "image_urls": list(p.image_urls),
                    "created_at": p.created_at,
                    "updated_at": p.updated_at,
                }
                for p in response.products
            ]
        except grpc.aio.AioRpcError as exc:
            logger.error("Get seller products gRPC call failed for seller_id=%s: %s", seller_id, exc)
            raise

    async def get_seller_stats(self, seller_id: str) -> dict:
        """Get seller statistics."""
        if not self._channel:
            raise grpc.aio.AioRpcError(code=grpc.StatusCode.UNAVAILABLE)

        from src.grpc_client._seller_pb2 import GetSellerStatsRequest
        from src.grpc_client._seller_pb2_grpc import SellerStub

        stub = SellerStub(self._channel)
        try:
            response = await stub.GetSellerStats(
                GetSellerStatsRequest(seller_id=seller_id),
                timeout=5.0,
            )
            return {
                "seller_id": response.seller_id,
                "total_orders": response.total_orders,
                "pending_orders": response.pending_orders,
                "processing_orders": response.processing_orders,
                "shipped_orders": response.shipped_orders,
                "delivered_orders": response.delivered_orders,
                "cancelled_orders": response.cancelled_orders,
                "total_revenue": response.total_revenue,
                "average_order_value": response.average_order_value,
                "rating": response.rating,
                "total_ratings": response.total_ratings,
                "total_products": response.total_products,
                "active_products": response.active_products,
                "low_stock_products": response.low_stock_products,
                "monthly_revenue": response.monthly_revenue,
                "monthly_orders": response.monthly_orders,
                "revenue_growth_rate": response.revenue_growth_rate,
            }
        except grpc.aio.AioRpcError as exc:
            logger.error("Get seller stats gRPC call failed for seller_id=%s: %s", seller_id, exc)
            raise

    @property
    def is_connected(self) -> bool:
        return self._channel is not None and self._channel._connected
