"""gRPC client for the Order service."""

import logging
from typing import Optional

import grpc

from src.config import settings

logger = logging.getLogger(__name__)

_ORDER_CHANNEL: Optional[grpc.aio.Channel] = None


def _get_order_channel() -> grpc.aio.Channel:
    """Return a cached gRPC channel to the Order service."""
    global _ORDER_CHANNEL
    if _ORDER_CHANNEL is None:
        _ORDER_CHANNEL = grpc.aio.insecure_channel(
            f"{settings.order_service_host}:{settings.order_service_port}"
        )
    return _ORDER_CHANNEL


async def get_seller_orders(
    seller_id: str,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Retrieve paginated orders for a given seller.

    Returns a dict with ``orders`` (list) and ``total`` (int).
    """
    channel = _get_order_channel()
    from src.grpc_client._order_pb2 import GetSellerOrdersRequest
    from src.grpc_client._order_pb2_grpc import OrderStub

    stub = OrderStub(channel)
    try:
        request = GetSellerOrdersRequest(
            seller_id=seller_id,
            page=page,
            page_size=page_size,
        )
        response = await stub.GetSellerOrders(request, timeout=5.0)
        return {
            "orders": [
                {
                    "id": str(o.id),
                    "seller_id": str(o.seller_id),
                    "buyer_id": str(o.buyer_id),
                    "status": o.status,
                    "total_amount": o.total_amount,
                    "created_at": o.created_at,
                }
                for o in response.orders
            ],
            "total": response.total,
            "page": response.page,
            "page_size": response.page_size,
        }
    except grpc.aio.AioRpcError as exc:
        logger.error("Order service gRPC error for seller %s: %s", seller_id, exc)
        return {"orders": [], "total": 0, "page": page, "page_size": page_size}
    except Exception:  # noqa: BLE001
        logger.exception("Unexpected error fetching orders for seller %s", seller_id)
        return {"orders": [], "total": 0, "page": page, "page_size": page_size}
