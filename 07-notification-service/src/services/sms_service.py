"""SMS notification service (stub for external SMS gateway)."""

import logging
from typing import Any

from src.config import settings

logger = logging.getLogger(__name__)


class SmsService:
    """Sends SMS notifications via an external gateway (e.g. Twilio, Vonage).

    In production this would call the gateway's REST API.  For now it
    logs the intended message so that integration tests can verify
    the call chain.
    """

    async def send_order_status_sms(
        self,
        phone: str,
        order_id: str,
        status: str,
    ) -> dict[str, Any]:
        """Send an SMS about an order status change."""
        message = f"Order {order_id} status: {status}"
        logger.info("SMS to %s: %s", phone, message)
        return {"to": phone, "status": "sent", "message": message}

    async def send_payment_sms(
        self,
        phone: str,
        amount: float,
        status: str,
    ) -> dict[str, Any]:
        """Send an SMS about a payment event."""
        message = f"Payment of ${amount:.2f} — {status}"
        logger.info("SMS to %s: %s", phone, message)
        return {"to": phone, "status": "sent", "message": message}
