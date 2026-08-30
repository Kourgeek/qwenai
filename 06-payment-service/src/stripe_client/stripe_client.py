"""
Async wrapper around the Stripe SDK for payment operations.

Provides create_payment_intent, confirm_payment, and refund_payment
against the Stripe API.  All methods are async via ``stripe.httpx_client``
under the hood (Stripe SDK >= 5.0 supports async natively).
"""

from __future__ import annotations

import logging
from typing import Any

import stripe
from stripe import StripeError

from src.config import settings

logger = logging.getLogger(__name__)


class StripeClient:
    """Thin async wrapper around Stripe's Python SDK."""

    def __init__(self, secret_key: str | None = None) -> None:
        self._secret_key = secret_key or settings.stripe_secret_key
        stripe.api_key = self._secret_key

    # ------------------------------------------------------------------
    # Payment Intent
    # ------------------------------------------------------------------

    async def create_payment_intent(
        self,
        amount: int,  # smallest currency unit (e.g. kopeks)
        currency: str = "rub",
        payment_method_types: list[str] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create a new PaymentIntent and return its dict representation."""
        try:
            pi = await stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                payment_method_types=payment_method_types or ["card"],
                metadata=metadata or {},
            )
            logger.info("Stripe PaymentIntent created: id=%s", pi.id)
            return pi
        except StripeError as exc:
            logger.error("Stripe create_payment_intent failed: %s", exc)
            raise

    async def confirm_payment(
        self,
        payment_intent_id: str,
        payment_method_id: str | None = None,
    ) -> dict[str, Any]:
        """Confirm (capture) an existing PaymentIntent."""
        try:
            if payment_method_id:
                pi = await stripe.PaymentIntent.confirm(
                    payment_intent_id,
                    payment_method=payment_method_id,
                )
            else:
                pi = await stripe.PaymentIntent.confirm(payment_intent_id)
            logger.info("Stripe PaymentIntent confirmed: id=%s status=%s", pi.id, pi.status)
            return pi
        except StripeError as exc:
            logger.error("Stripe confirm_payment failed: %s", exc)
            raise

    async def get_payment_intent(self, payment_intent_id: str) -> dict[str, Any]:
        """Retrieve a PaymentIntent by ID."""
        try:
            pi = await stripe.PaymentIntent.retrieve(payment_intent_id)
            return pi
        except StripeError as exc:
            logger.error("Stripe get_payment_intent failed: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Refund
    # ------------------------------------------------------------------

    async def refund_payment(
        self,
        payment_intent_id: str,
        amount: int | None = None,
        reason: str = "requested_by_customer",
    ) -> dict[str, Any]:
        """Create a refund for a PaymentIntent."""
        try:
            refund = await stripe.Refund.create(
                payment_intent=payment_intent_id,
                amount=amount,
                reason=reason,
            )
            logger.info("Stripe refund created: id=%s for PaymentIntent %s", refund.id, payment_intent_id)
            return refund
        except StripeError as exc:
            logger.error("Stripe refund_payment failed: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Webhook
    # ------------------------------------------------------------------

    @staticmethod
    def construct_webhook_event(payload: bytes, signature: str) -> stripe.WebhookEvent:
        """Verify and construct a Stripe webhook event."""
        try:
            return stripe.Webhook.construct_event(
                payload,
                signature,
                settings.stripe_webhook_secret,
            )
        except (stripe.SignatureVerificationError, ValueError) as exc:
            logger.error("Stripe webhook signature verification failed: %s", exc)
            raise


# Singleton
stripe_client = StripeClient()
