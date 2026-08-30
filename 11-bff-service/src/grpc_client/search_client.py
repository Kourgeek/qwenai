"""gRPC client for Search service.

Handles product search queries via Search service gRPC interface.
"""

import grpc
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SearchGrpcClient:
    """Client for Search service gRPC communication."""

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
        """Search products by query string.

        Args:
            query: Search query text.
            limit: Max results to return.
            offset: Pagination offset.
            category_id: Optional category filter.
            min_price: Optional minimum price filter.
            max_price: Optional maximum price filter.
            sort_by: Sort field (relevance, price_asc, price_desc, newest).

        Returns:
            Dict with products list and pagination info.

        Raises:
            grpc.aio.AioRpcError: If gRPC call fails.
        """
        if not self._channel:
            raise grpc.aio.AioRpcError(code=grpc.StatusCode.UNAVAILABLE)

        from src.grpc_client._search_pb2 import SearchRequest
        from src.grpc_client._search_pb2_grpc import SearchStub

        stub = SearchStub(self._channel)
        try:
            response = await stub.Search(
                SearchRequest(
                    query=query,
                    limit=limit,
                    offset=offset,
                    category_id=category_id or "",
                    min_price=min_price or 0.0,
                    max_price=max_price or 0.0,
                    sort_by=sort_by,
                ),
                timeout=10.0,
            )
            products = [
                {
                    "product_id": p.product_id,
                    "name": p.name,
                    "description": p.description,
                    "price": p.price,
                    "currency": p.currency,
                    "category_id": p.category_id,
                    "seller_id": p.seller_id,
                    "rating": p.rating,
                    "image_url": p.image_url,
                    "relevance_score": p.relevance_score,
                }
                for p in response.products
            ]
            return {
                "products": products,
                "total_count": response.total_count,
                "query": query,
                "limit": limit,
                "offset": offset,
            }
        except grpc.aio.AioRpcError as exc:
            logger.error("Search gRPC call failed for query='%s': %s", query, exc)
            raise

    @property
    def is_connected(self) -> bool:
        return self._channel is not None and self._channel._connected
