"""
Async wrapper for YooMoney (YooKassa) payment provider.

Provides create_payment, confirm_payment, and refund_payment.
All HTTP calls use ``httpx.AsyncClient`` for true async operation.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any

import httpx

from src.config import settings

logger = logging.getLogger(__name__)

# YooMoney API base URL
YOOMONEY_API_URL = "https://api.yoomoney.ru"


class YooMoneyClient:
    """Thin async wrapper around YooMoney REST API."""

    def __init__(
        self,
        shop_id: str | None = None,
        token: str | None = None,
    ) -> None:
        self._shop_id = shop_id or settings.yoomoney_shop_id
        self._token = token or settings.yoomoney_token

    # ------------------------------------------------------------------
    # Payment
    # ------------------------------------------------------------------

    async def create_payment(
        self,
        amount: float,
        order_id: str,
        description: str = "",
        confirmation_url: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new payment request in YooMoney.

        Returns the payment object including the confirmation URL.
        """
        confirmation_url = confirmation_url or settings.yoomoney_confirmation_url

        # YooMoney uses a unique confirmation token per payment
        confirmation_token = hashlib.sha256(f"{order_id}{amount}".encode()).hexdigest()

        payload = {
            "action": "full-authorize",
            "amount": {"value": str(amount), "currency": "RUB"},
            "confirmation": {
                "type": "redirect",
                "return_url": confirmation_url,
            },
            "invoice": {
                "invoice_id": order_id,
                "description": description or f"Order {order_id}",
            },
            "capture": True,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{YOOMONEY_API_URL}/quickpay/confirm.json",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json",
                    "Idempotence-Key": confirmation_token,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        logger.info("YooMoney payment created: id=%s for order %s", data.get("id"), order_id)
        return data

    async def confirm_payment(self, payment_id: str) -> dict[str, Any]:
        """
        Confirm (capture) an existing YooMoney payment.

        For redirect-based flows confirmation is typically done by the
        user on YooMoney's side; this method allows server-side capture
        when needed.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{YOOMONEY_API_URL}/payment-over/{payment_id}/status",
                headers={"Authorization": f"Bearer {self._token}"},
            )
            resp.raise_for_status()
            data = resp.json()

        logger.info("YooMoney payment confirmed: id=%s status=%s", payment_id, data.get("status"))
        return data

    # ------------------------------------------------------------------
    # Refund
    # ------------------------------------------------------------------

    async def refund_payment(
        self,
        payment_id: str,
        amount: float,
        reason: str = "requested_by_customer",
    ) -> dict[str, Any]:
        """Issue a refund for a YooMoney payment."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{YOOMONEY_API_URL}/refund/{payment_id}",
                json={
                    "amount": {"value": str(amount), "currency": "RUB"},
                    "description": reason,
                },
                headers={"Authorization": f"Bearer {self._token}"},
            )
            resp.raise_for_status()
            data = resp.json()

        logger.info("YooMoney refund created: id=%s for payment %s", data.get("operation_id"), payment_id)
        return data

    # ------------------------------------------------------------------
    # Webhook verification
    # ------------------------------------------------------------------

    @staticmethod
    def verify_webhook_signature(
        signature: str,
        body: bytes,
        secret: str,
    ) -> bool:
        """
        Verify YooMoney webhook signature.

        YooMoney sends an ``X-Notification-Checksum`` header with
        SHA256 HMAC of the request body.
        """
        computed = hmac.new(
            secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(computed.lower(), signature.lower())


# Singleton
yoomoney_client = YooMoneyClient()
