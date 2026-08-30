"""gRPC client for the Order Service."""

from dataclasses import dataclass

import grpc

from src.config import settings


@dataclass(kw_only=True)
class OrderFilter:
    status: str | None = None
    seller_id: str | None = None
    buyer_id: str | None = None
    page: int = 1
    page_size: int = 50


async def get_order(order_id: str) -> dict | None:
    """Fetch a single order by ID from the Order Service."""
    async with grpc.aio.insecure_channel(f"{settings.order_service_host}:{settings.order_service_port}") as channel:
        # Placeholder: replace with the real stub call once the proto
        # definition for OrderService is available.
        # Example target:
        #   stub = order_pb2_grpc.OrderServiceStub(channel)
        #   resp = await stub.GetOrder(order_pb2.GetOrderRequest(id=order_id))
        #   return _proto_to_dict(resp.order) if resp.HasField("order") else None
        return None


async def list_orders(filters: OrderFilter | None = None) -> list[dict]:
    """List orders with optional filters from the Order Service."""
    if filters is None:
        filters = OrderFilter()

    async with grpc.aio.insecure_channel(f"{settings.order_service_host}:{settings.order_service_port}") as channel:
        # Placeholder: replace with the real stub call.
        # Example target:
        #   stub = order_pb2_grpc.OrderServiceStub(channel)
        #   resp = await stub.ListOrders(
        #       order_pb2.ListOrdersRequest(
        #           status=filters.status,
        #           seller_id=filters.seller_id,
        #           buyer_id=filters.buyer_id,
        #           page=filters.page,
        #           page_size=filters.page_size,
        #       )
        #   )
        #   return [_proto_to_dict(o) for o in resp.orders]
        return []
