"""
PaymentService — core business logic for payment operations.

Orchestrates the Stripe/YooMoney providers, repositories, and Kafka
event publishing to implement the payment lifecycle:

    PENDING → PROCESSING → COMPLETED / FAILED
    COMPLETED → REFUNDED
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.kafka.producer import PaymentKafkaProducer, payment_kafka_producer
from src.models.payment import (
    Payment,
    PaymentMethod,
    PaymentProvider,
    PaymentStatus,
    Refund,
    RefundStatus,
)
from src.repositories.payment_method_repository import PaymentMethodRepository
from src.repositories.payment_repository import PaymentRepository
from src.repositories.refund_repository import RefundRepository
from src.stripe_client.stripe_client import StripeClient, stripe_client
from src.stripe_client.yoomoney_client import YooMoneyClient, yoomoney_client

logger = logging.getLogger(__name__)


class PaymentService:
    """Stateless service class; all I/O is injected or configured."""

    def __init__(
        self,
        session: AsyncSession,
        stripe_client: StripeClient | None = None,
        yoomoney_client: YooMoneyClient | None = None,
        kafka_producer: PaymentKafkaProducer | None = None,
    ) -> None:
        self._session = session
        self._stripe = stripe_client or stripe_client
        self._yoomoney = yoomoney_client or yoomoney_client
        self._kafka = kafka_producer or payment_kafka_producer
        self._payment_repo = PaymentRepository(session)
        self._payment_method_repo = PaymentMethodRepository(session)
        self._refund_repo = RefundRepository(session)

    # ------------------------------------------------------------------
    # create_payment
    # ------------------------------------------------------------------

    async def create_payment(
        self,
        order_id: str,
        user_id: UUID,
        amount: float,
        currency: str = "RUB",
        provider: PaymentProvider = PaymentProvider.STRIPE,
        payment_method_id: UUID | None = None,
        description: str = "",
    ) -> Payment:
        """
        Create a new payment and initiate the provider-side flow.

        Returns the persisted Payment row.
        """
        # 1. Check for existing payment for this order
        existing = await self._payment_repo.get_by_order_id(order_id)
        if existing is not None:
            raise ValueError(f"Payment already exists for order_id={order_id}")

        payment_id = uuid4()
        payment = Payment(
            id=payment_id,
            order_id=order_id,
            user_id=user_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PENDING,
            provider=provider,
            payment_method_id=payment_method_id,
        )

        # 2. Persist
        payment = await self._payment_repo.create(payment)

        # 3. Delegate to provider
        try:
            if provider == PaymentProvider.STRIPE:
                provider_data = await self._stripe.create_payment_intent(
                    amount=int(amount * 100),  # convert to kopeks
                    currency=currency.lower(),
                    metadata={"order_id": order_id, "user_id": str(user_id)},
                )
                payment.provider_payment_id = provider_data.get("id")
                await self._payment_repo.update_status(
                    payment.id,
                    PaymentStatus.PROCESSING,
                    provider_payment_id=payment.provider_payment_id,
                )
            elif provider == PaymentProvider.YOOMONEY:
                provider_data = await self._yoomoney.create_payment(
                    amount=amount,
                    order_id=order_id,
                    description=description,
                    confirmation_url=settings.yoomoney_confirmation_url,
                )
                payment.provider_payment_id = provider_data.get("id")
                await self._payment_repo.update_status(
                    payment.id,
                    PaymentStatus.PROCESSING,
                    provider_payment_id=payment.provider_payment_id,
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")

            await self._session.flush()
        except Exception as exc:
            logger.error("Failed to create payment with provider %s: %s", provider, exc)
            await self._payment_repo.update_status(payment.id, PaymentStatus.FAILED, provider_error=str(exc))
            await self._session.flush()
            await self._kafka.publish_payment_failed(payment_id=str(payment.id), order_id=order_id, error=str(exc))
            raise

        return payment

    # ------------------------------------------------------------------
    # confirm_payment
    # ------------------------------------------------------------------

    async def confirm_payment(self, payment_id: UUID) -> Payment:
        """
        Confirm (capture) a payment that is in PROCESSING state.
        """
        payment = await self._payment_repo.get_by_id(payment_id)
        if payment is None:
            raise ValueError(f"Payment {payment_id} not found")
        if payment.status not in (PaymentStatus.PENDING, PaymentStatus.PROCESSING):
            raise ValueError(f"Cannot confirm payment in state {payment.status.value}")

        try:
            if payment.provider == PaymentProvider.STRIPE:
                provider_data = await self._stripe.confirm_payment(payment.provider_payment_id)
                status_str = provider_data.get("status", "")
                if status_str == "succeeded":
                    new_status = PaymentStatus.COMPLETED
                elif status_str == "requires_payment_method":
                    new_status = PaymentStatus.FAILED
                else:
                    new_status = PaymentStatus.PROCESSING
            elif payment.provider == PaymentProvider.YOOMONEY:
                await self._yoomoney.confirm_payment(payment.provider_payment_id)
                new_status = PaymentStatus.COMPLETED
            else:
                raise ValueError(f"Unsupported provider: {payment.provider}")

            payment = await self._payment_repo.update_status(
                payment_id,
                new_status,
                paid_at=datetime.now(timezone.utc),
            )
            await self._session.flush()

            # Publish domain event
            await self._kafka.publish_payment_completed(
                payment_id=str(payment.id),
                order_id=payment.order_id,
                amount=float(payment.amount),
                currency=payment.currency,
                provider=payment.provider.value,
            )
        except Exception as exc:
            logger.error("Failed to confirm payment %s: %s", payment_id, exc)
            await self._payment_repo.update_status(payment_id, PaymentStatus.FAILED, provider_error=str(exc))
            await self._session.flush()
            await self._kafka.publish_payment_failed(
                payment_id=str(payment_id),
                order_id=payment.order_id if payment else "unknown",
                error=str(exc),
            )
            raise

        return payment

    # ------------------------------------------------------------------
    # get_payment
    # ------------------------------------------------------------------

    async def get_payment(self, payment_id: UUID) -> Payment:
        payment = await self._payment_repo.get_by_id(payment_id)
        if payment is None:
            raise ValueError(f"Payment {payment_id} not found")
        return payment

    # ------------------------------------------------------------------
    # refund_payment
    # ------------------------------------------------------------------

    async def refund_payment(
        self,
        payment_id: UUID,
        user_id: UUID,
        amount: float | None = None,
        reason: str = "requested_by_customer",
    ) -> Refund:
        """
        Initiate a refund for a completed payment.
        """
        payment = await self._payment_repo.get_by_id(payment_id)
        if payment is None:
            raise ValueError(f"Payment {payment_id} not found")
        if payment.status != PaymentStatus.COMPLETED:
            raise ValueError(f"Cannot refund payment in state {payment.status.value}")

        refund_amount = amount if amount is not None else float(payment.amount)

        refund_id = uuid4()
        refund = Refund(
            id=refund_id,
            payment_id=payment_id,
            user_id=user_id,
            amount=refund_amount,
            currency=payment.currency,
            status=RefundStatus.PENDING,
            reason=reason,
        )
        refund = await self._refund_repo.create(refund)

        try:
            if payment.provider == PaymentProvider.STRIPE:
                provider_data = await self._stripe.refund_payment(
                    payment.provider_payment_id,
                    amount=int(refund_amount * 100),
                    reason=reason,
                )
                await self._refund_repo.update_status(
                    refund.id,
                    RefundStatus.COMPLETED,
                    provider_refund_id=provider_data.get("id"),
                    refunded_at=datetime.now(timezone.utc),
                )
                await self._payment_repo.update_status(payment_id, PaymentStatus.REFUNDED)
                await self._session.flush()
            elif payment.provider == PaymentProvider.YOOMONEY:
                provider_data = await self._yoomoney.refund_payment(
                    payment.provider_payment_id,
                    amount=refund_amount,
                    reason=reason,
                )
                await self._refund_repo.update_status(
                    refund.id,
                    RefundStatus.COMPLETED,
                    provider_refund_id=provider_data.get("operation_id"),
                    refunded_at=datetime.now(timezone.utc),
                )
                await self._payment_repo.update_status(payment_id, PaymentStatus.REFUNDED)
                await self._session.flush()
            else:
                raise ValueError(f"Unsupported provider: {payment.provider}")

        except Exception as exc:
            logger.error("Refund failed for payment %s: %s", payment_id, exc)
            await self._refund_repo.update_status(refund.id, RefundStatus.FAILED, provider_refund_id="")
            await self._session.flush()
            raise

        return refund

    # ------------------------------------------------------------------
    # get_user_payments
    # ------------------------------------------------------------------

    async def get_user_payments(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Payment]:
        return await self._payment_repo.list_by_user(user_id, limit=limit, offset=offset)

    # ------------------------------------------------------------------
    # webhook
    # ------------------------------------------------------------------

    async def handle_webhook(
        self,
        provider: str,
        payload: bytes,
        signature: str,
    ) -> dict[str, Any]:
        """
        Dispatch webhook to the appropriate provider verifier.

        Returns a JSON-serialisable response dict.
        """
        if provider == "stripe":
            return await self._handle_stripe_webhook(payload, signature)
        elif provider == "yoomoney":
            return await self._handle_yoomoney_webhook(payload, signature)
        else:
            raise ValueError(f"Unknown webhook provider: {provider}")

    async def _handle_stripe_webhook(
        self,
        payload: bytes,
        signature: str,
    ) -> dict[str, Any]:
        event = self._stripe.construct_webhook_event(payload, signature)

        if event.type == "payment_intent.succeeded":
            pi_data = event.data.object
            payment = await self._payment_repo.get_by_provider_payment_id(pi_data.get("id"))
            if payment:
                await self._payment_repo.update_status(
                    payment.id,
                    PaymentStatus.COMPLETED,
                    paid_at=datetime.now(timezone.utc),
                )
                await self._session.flush()
                await self._kafka.publish_payment_completed(
                    payment_id=str(payment.id),
                    order_id=payment.order_id,
                    amount=float(payment.amount),
                    currency=payment.currency,
                    provider="STRIPE",
                )
        elif event.type == "payment_intent.payment_failed":
            pi_data = event.data.object
            payment = await self._payment_repo.get_by_provider_payment_id(pi_data.get("id"))
            if payment:
                error_msg = pi_data.get("last_payment_error", {}).get("message", "Unknown error") if pi_data.get("last_payment_error") else "Payment failed"
                await self._payment_repo.update_status(payment.id, PaymentStatus.FAILED, provider_error=error_msg)
                await self._session.flush()
                await self._kafka.publish_payment_failed(
                    payment_id=str(payment.id),
                    order_id=payment.order_id,
                    error=error_msg,
                )

        return {"status": "ok"}

    async def _handle_yoomoney_webhook(
        self,
        payload: bytes,
        signature: str,
    ) -> dict[str, Any]:
        """
        Verify YooMoney webhook signature and process the notification.

        YooMoney sends POST with JSON body and X-Notification-Checksum header.
        """
        if not yoomoney_client.verify_webhook_signature(signature, payload, settings.yoomoney_token):
            raise ValueError("YooMoney webhook signature verification failed")

        data = json.loads(payload)
        # YooMoney status fields
        status = data.get("event_type", "")
        invoice_id = data.get("invoice", {}).get("invoice_id")

        if status in ("payment_succeeded", "payment_canceled"):
            payment = await self._payment_repo.get_by_order_id(invoice_id)
            if payment:
                new_status = PaymentStatus.COMPLETED if status == "payment_succeeded" else PaymentStatus.FAILED
                await self._payment_repo.update_status(
                    payment.id,
                    new_status,
                    paid_at=datetime.now(timezone.utc) if status == "payment_succeeded" else None,
                )
                await self._session.flush()

        return {"status": "ok"}
