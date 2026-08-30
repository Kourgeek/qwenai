"""
gRPC service implementation for the Payment domain.

Implements the generated ``PaymentServiceServicer`` and routes
gRPC calls through ``PaymentService`` business logic.
"""

from __future__ import annotations

import logging
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

# Import the generated protobuf stubs
# Run: grpc_tools.protoc -Iprotos --python_out=. --grpc_python_out=. protos/payment.proto
from src.grpc_server import payment_pb2, payment_pb2_grpc
from src.database import async_session_factory
from src.models.payment import PaymentProvider, PaymentStatus, RefundStatus
from src.services.payment_service import PaymentService

logger = logging.getLogger(__name__)


class PaymentServiceServicer(payment_pb2_grpc.PaymentServiceServicer):
    """gRPC implementation of the PaymentService API."""

    # ------------------------------------------------------------------
    # CreatePayment
    # ------------------------------------------------------------------

    async def CreatePayment(self, request, context):
        try:
            async with async_session_factory() as session:
                service = PaymentService(session=session)
                provider = PaymentProvider(request.provider) if request.provider else PaymentProvider.STRIPE
                payment = await service.create_payment(
                    order_id=request.order_id,
                    user_id=UUID(request.user_id) if request.user_id else uuid4(),
                    amount=float(request.amount),
                    currency=request.currency or "RUB",
                    provider=provider,
                    description=request.description,
                )
                return payment_pb2.PaymentResponse(
                    payment_id=str(payment.id),
                    order_id=payment.order_id,
                    status=payment.status.value,
                    amount=str(payment.amount),
                    currency=payment.currency,
                    provider=payment.provider.value,
                    provider_payment_id=payment.provider_payment_id or "",
                )
        except ValueError as exc:
            context.set_code(context.code().INVALID_ARGUMENT)
            context.set_details(str(exc))
            return payment_pb2.PaymentResponse()
        except Exception as exc:
            logger.error("gRPC CreatePayment error: %s", exc)
            context.set_code(context.code().INTERNAL)
            context.set_details(str(exc))
            return payment_pb2.PaymentResponse()

    # ------------------------------------------------------------------
    # ConfirmPayment
    # ------------------------------------------------------------------

    async def ConfirmPayment(self, request, context):
        try:
            async with async_session_factory() as session:
                service = PaymentService(session=session)
                payment = await service.confirm_payment(UUID(request.payment_id))
                return payment_pb2.PaymentResponse(
                    payment_id=str(payment.id),
                    order_id=payment.order_id,
                    status=payment.status.value,
                    amount=str(payment.amount),
                    currency=payment.currency,
                    provider=payment.provider.value,
                    provider_payment_id=payment.provider_payment_id or "",
                )
        except ValueError as exc:
            context.set_code(context.code().NOT_FOUND)
            context.set_details(str(exc))
            return payment_pb2.PaymentResponse()
        except Exception as exc:
            logger.error("gRPC ConfirmPayment error: %s", exc)
            context.set_code(context.code().INTERNAL)
            context.set_details(str(exc))
            return payment_pb2.PaymentResponse()

    # ------------------------------------------------------------------
    # GetPayment
    # ------------------------------------------------------------------

    async def GetPayment(self, request, context):
        try:
            async with async_session_factory() as session:
                service = PaymentService(session=session)
                payment = await service.get_payment(UUID(request.payment_id))
                return payment_pb2.PaymentResponse(
                    payment_id=str(payment.id),
                    order_id=payment.order_id,
                    status=payment.status.value,
                    amount=str(payment.amount),
                    currency=payment.currency,
                    provider=payment.provider.value,
                    provider_payment_id=payment.provider_payment_id or "",
                )
        except ValueError as exc:
            context.set_code(context.code().NOT_FOUND)
            context.set_details(str(exc))
            return payment_pb2.PaymentResponse()
        except Exception as exc:
            logger.error("gRPC GetPayment error: %s", exc)
            context.set_code(context.code().INTERNAL)
            context.set_details(str(exc))
            return payment_pb2.PaymentResponse()

    # ------------------------------------------------------------------
    # RefundPayment
    # ------------------------------------------------------------------

    async def RefundPayment(self, request, context):
        try:
            async with async_session_factory() as session:
                service = PaymentService(session=session)
                refund = await service.refund_payment(
                    payment_id=UUID(request.payment_id),
                    user_id=UUID(request.user_id),
                    amount=float(request.amount) if request.amount else None,
                    reason=request.reason,
                )
                return payment_pb2.RefundResponse(
                    refund_id=str(refund.id),
                    payment_id=str(refund.payment_id),
                    status=refund.status.value,
                    amount=str(refund.amount),
                    currency=refund.currency,
                    provider_refund_id=refund.provider_refund_id or "",
                )
        except ValueError as exc:
            context.set_code(context.code().INVALID_ARGUMENT)
            context.set_details(str(exc))
            return payment_pb2.RefundResponse()
        except Exception as exc:
            logger.error("gRPC RefundPayment error: %s", exc)
            context.set_code(context.code().INTERNAL)
            context.set_details(str(exc))
            return payment_pb2.RefundResponse()

    # ------------------------------------------------------------------
    # GetUserPayments
    # ------------------------------------------------------------------

    async def GetUserPayments(self, request, context):
        try:
            async with async_session_factory() as session:
                service = PaymentService(session=session)
                payments = await service.get_user_payments(
                    user_id=UUID(request.user_id),
                    limit=request.limit if request.limit > 0 else 50,
                    offset=request.offset,
                )
                responses = [
                    payment_pb2.PaymentResponse(
                        payment_id=str(p.id),
                        order_id=p.order_id,
                        status=p.status.value,
                        amount=str(p.amount),
                        currency=p.currency,
                        provider=p.provider.value,
                        provider_payment_id=p.provider_payment_id or "",
                    )
                    for p in payments
                ]
                return payment_pb2.PaymentListResponse(payments=responses)
        except ValueError as exc:
            context.set_code(context.code().NOT_FOUND)
            context.set_details(str(exc))
            return payment_pb2.PaymentListResponse()
        except Exception as exc:
            logger.error("gRPC GetUserPayments error: %s", exc)
            context.set_code(context.code().INTERNAL)
            context.set_details(str(exc))
            return payment_pb2.PaymentListResponse()

    # ------------------------------------------------------------------
    # Webhook
    # ------------------------------------------------------------------

    async def Webhook(self, request, context):
        """
        gRPC endpoint for webhook delivery (alternative to HTTP).
        """
        try:
            async with async_session_factory() as session:
                service = PaymentService(session=session)
                result = await service.handle_webhook(
                    provider=request.provider,
                    payload=request.payload.encode("utf-8") if request.payload else b"",
                    signature=request.signature,
                )
                return payment_pb2.WebhookResponse(status=result.get("status", "ok"))
        except ValueError as exc:
            context.set_code(context.code().INVALID_ARGUMENT)
            context.set_details(str(exc))
            return payment_pb2.WebhookResponse()
        except Exception as exc:
            logger.error("gRPC Webhook error: %s", exc)
            context.set_code(context.code().INTERNAL)
            context.set_details(str(exc))
            return payment_pb2.WebhookResponse()
