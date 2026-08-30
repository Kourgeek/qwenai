"""gRPC client for the Seller Service."""

from dataclasses import dataclass

import grpc

from src.config import settings


@dataclass(kw_only=True)
class SellerFilter:
    status: str | None = None
    country: str | None = None
    page: int = 1
    page_size: int = 50


async def get_seller(seller_id: str) -> dict | None:
    """Fetch a single seller by ID from the Seller Service."""
    async with grpc.aio.insecure_channel(f"{settings.seller_service_host}:{settings.seller_service_port}") as channel:
        # Placeholder: replace with the real stub call once the proto
        # definition for SellerService is available.
        # Example target:
        #   stub = seller_pb2_grpc.SellerServiceStub(channel)
        #   resp = await stub.GetSeller(seller_pb2.GetSellerRequest(id=seller_id))
        #   return _proto_to_dict(resp.seller) if resp.HasField("seller") else None
        return None


async def list_sellers(filters: SellerFilter | None = None) -> list[dict]:
    """List sellers with optional filters from the Seller Service."""
    if filters is None:
        filters = SellerFilter()

    async with grpc.aio.insecure_channel(f"{settings.seller_service_host}:{settings.seller_service_port}") as channel:
        # Placeholder: replace with the real stub call.
        # Example target:
        #   stub = seller_pb2_grpc.SellerServiceStub(channel)
        #   resp = await stub.ListSellers(
        #       seller_pb2.ListSellersRequest(
        #           status=filters.status,
        #           country=filters.country,
        #           page=filters.page,
        #           page_size=filters.page_size,
        #       )
        #   )
        #   return [_proto_to_dict(s) for s in resp.sellers]
        return []
