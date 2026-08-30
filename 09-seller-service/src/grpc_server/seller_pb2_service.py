"""gRPC service implementation for Seller operations.

This module wires the protobuf-generated gRPC service class to the
SellerService business-logic layer.
"""

import logging
import uuid

from google.protobuf.empty_pb2 import Empty
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session_factory
from src.services.seller_service import SellerService, SellerNotFoundError, SellerValidationError

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Re-export for registration in the gRPC server
# ------------------------------------------------------------------

from src.grpc_server import seller_pb2
from src.grpc_server import seller_pb2_grpc


class SellerServiceServicer(seller_pb2_grpc.SellerServiceServicer):
    """Implements the SellerService gRPC RPCs."""

    def __init__(self) -> None:
        self._service = SellerService()

    # -- RegisterSeller ------------------------------------------------

    async def RegisterSeller(self, request, context):
        try:
            seller_id = uuid.UUID(request.user_id) if request.user_id else uuid.uuid4()
            async with async_session_factory() as session:
                result = await self._service.register_seller(
                    session=session,
                    user_id=seller_id,
                    company_name=request.company_name,
                    inn=request.inn,
                    kpp=request.kpp or None,
                    bank_name=request.bank_name or None,
                    bank_account=request.bank_account or None,
                    bank_bik=request.bank_bik or None,
                    token=request.token or None,
                )
                return seller_pb2.SellerResponse(
                    id=str(uuid.uuid4()),  # id will be set by DB
                    status="OK",
                    message="Seller registered successfully",
                    seller_data=seller_pb2.SellerData(**result),
                )
        except SellerValidationError as exc:
            context.abort(400, str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.exception("RegisterSeller error")
            context.abort(500, str(exc))

    # -- GetSeller -----------------------------------------------------

    async def GetSeller(self, request, context):
        try:
            seller_id = uuid.UUID(request.id)
            async with async_session_factory() as session:
                result = await self._service.get_seller(session, seller_id)
                return seller_pb2.SellerResponse(
                    id=str(seller_id),
                    status="OK",
                    message="Seller retrieved successfully",
                    seller_data=seller_pb2.SellerData(**result),
                )
        except SellerNotFoundError:
            context.abort(404, "Seller not found")
        except Exception as exc:  # noqa: BLE001
            logger.exception("GetSeller error")
            context.abort(500, str(exc))

    # -- UpdateSeller --------------------------------------------------

    async def UpdateSeller(self, request, context):
        try:
            seller_id = uuid.UUID(request.id)
            async with async_session_factory() as session:
                result = await self._service.update_seller(
                    session,
                    seller_id,
                    token=request.token or None,
                    company_name=request.company_name or None,
                    kpp=request.kpp or None,
                    bank_name=request.bank_name or None,
                    bank_account=request.bank_account or None,
                    bank_bik=request.bank_bik or None,
                )
                return seller_pb2.SellerResponse(
                    id=str(seller_id),
                    status="OK",
                    message="Seller updated successfully",
                    seller_data=seller_pb2.SellerData(**result),
                )
        except SellerNotFoundError:
            context.abort(404, "Seller not found")
        except SellerValidationError as exc:
            context.abort(400, str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.exception("UpdateSeller error")
            context.abort(500, str(exc))

    # -- GetSellerProducts ---------------------------------------------

    async def GetSellerProducts(self, request, context):
        try:
            seller_id = uuid.UUID(request.seller_id)
            products = await self._service.get_seller_products(seller_id)
            product_data = [
                seller_pb2.ProductInfo(
                    id=p.get("id", ""),
                    seller_id=p.get("seller_id", ""),
                    name=p.get("name", ""),
                    description=p.get("description", ""),
                    price=p.get("price", 0),
                    category_id=p.get("category_id", ""),
                    status=p.get("status", ""),
                )
                for p in products
            ]
            return seller_pb2.ProductsResponse(
                seller_id=str(seller_id),
                products=product_data,
                total=len(product_data),
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("GetSellerProducts error")
            context.abort(500, str(exc))

    # -- GetSellerOrders -----------------------------------------------

    async def GetSellerOrders(self, request, context):
        try:
            seller_id = uuid.UUID(request.seller_id)
            orders_data = await self._service.get_seller_orders(
                seller_id,
                page=request.page,
                page_size=request.page_size,
            )
            order_data = [
                seller_pb2.OrderInfo(
                    id=o.get("id", ""),
                    seller_id=o.get("seller_id", ""),
                    buyer_id=o.get("buyer_id", ""),
                    status=o.get("status", ""),
                    total_amount=o.get("total_amount", 0),
                    created_at=o.get("created_at", ""),
                )
                for o in orders_data.get("orders", [])
            ]
            return seller_pb2.OrdersResponse(
                seller_id=str(seller_id),
                orders=order_data,
                total=orders_data.get("total", 0),
                page=orders_data.get("page", 1),
                page_size=orders_data.get("page_size", 20),
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("GetSellerOrders error")
            context.abort(500, str(exc))

    # -- DeactivateSeller ----------------------------------------------

    async def DeactivateSeller(self, request, context):
        try:
            seller_id = uuid.UUID(request.id)
            async with async_session_factory() as session:
                result = await self._service.deactivate_seller(
                    session,
                    seller_id,
                    token=request.token or None,
                )
                return seller_pb2.SellerResponse(
                    id=str(seller_id),
                    status="OK",
                    message="Seller deactivated successfully",
                    seller_data=seller_pb2.SellerData(**result),
                )
        except SellerNotFoundError:
            context.abort(404, "Seller not found")
        except SellerValidationError as exc:
            context.abort(400, str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.exception("DeactivateSeller error")
            context.abort(500, str(exc))
