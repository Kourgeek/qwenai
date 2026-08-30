"""gRPC service implementation for Order domain RPCs."""

from __future__ import annotations

import logging
from typing import Any

import grpc
from grpc import ServicerContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session_factory
from src.kafka.publisher import OrderKafkaPublisher
from src.services.order_service import OrderService

# ── generated protobuf stubs (run ``grpc_tools.protoc``) ─────────────────
# Placeholder — replace with actual imports after codegen:
# from src.proto import order_pb2
# from src.proto import order_pb2_grpc

logger = logging.getLogger(__name__)


class OrderServicer:
    """Implements the Order gRPC service interface."""

    def __init__(self, kafka_publisher: OrderKafkaPublisher) -> None:
        self._order_service = OrderService(kafka_publisher=kafka_publisher)

    # ── helpers ──────────────────────────────────────────────────────────

    async def _make_session(self) -> AsyncSession:
        return async_session_factory()

    # ── RPCs ─────────────────────────────────────────────────────────────

    async def CreateOrder(
        self,
        request: Any,
        context: ServicerContext,
    ) -> Any:
        session: AsyncSession = await self._make_session()
        try:
            order = await self._order_service.create_order(
                session=session,
                user_id=request.user_id,
                cart_id=request.cart_id,
                shipping_address=dict(request.shipping_address) if request.shipping_address else None,
                payment_method=request.payment_method,
            )
            return {
                "id": order.id,
                "status": order.status,
                "total_amount": order.total_amount,
                "currency": order.currency,
            }
        except (ValueError, LookupError, PermissionError) as exc:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(exc))
            return {}
        finally:
            await session.close()

    async def GetOrder(
        self,
        request: Any,
        context: ServicerContext,
    ) -> Any:
        session: AsyncSession = await self._make_session()
        try:
            order = await self._order_service.get_order(session, request.order_id)
            if order is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Order {request.order_id} not found")
                return {}
            return {
                "id": order.id,
                "user_id": order.user_id,
                "status": order.status,
                "total_amount": order.total_amount,
                "currency": order.currency,
            }
        finally:
            await session.close()

    async def GetUserOrders(
        self,
        request: Any,
        context: ServicerContext,
    ) -> Any:
        session: AsyncSession = await self._make_session()
        try:
            orders = await self._order_service.get_user_orders(
                session,
                request.user_id,
                limit=request.limit or 20,
                offset=request.offset or 0,
            )
            return {
                "orders": [
                    {
                        "id": o.id,
                        "status": o.status,
                        "total_amount": o.total_amount,
                        "currency": o.currency,
                        "created_at": str(o.created_at),
                    }
                    for o in orders
                ]
            }
        finally:
            await session.close()

    async def CancelOrder(
        self,
        request: Any,
        context: ServicerContext,
    ) -> Any:
        session: AsyncSession = await self._make_session()
        try:
            order = await self._order_service.cancel_order(
                session,
                order_id=request.order_id,
                user_id=request.user_id,
                reason=request.reason,
            )
            return {
                "id": order.id,
                "status": order.status,
                "cancelled_at": str(order.cancelled_at) if order.cancelled_at else None,
            }
        except (ValueError, LookupError, PermissionError) as exc:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(exc))
            return {}
        finally:
            await session.close()

    async def UpdateOrderStatus(
        self,
        request: Any,
        context: ServicerContext,
    ) -> Any:
        session: AsyncSession = await self._make_session()
        try:
            order = await self._order_service.update_order_status(
                session,
                order_id=request.order_id,
                new_status=request.new_status,
            )
            return {
                "id": order.id,
                "status": order.status,
            }
        except (ValueError, LookupError) as exc:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(exc))
            return {}
        finally:
            await session.close()
