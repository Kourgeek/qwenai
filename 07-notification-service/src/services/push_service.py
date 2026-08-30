"""Push notification service (stub for FCM / APNs)."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class PushService:
    """Sends push notifications via FCM (Android) / APNs (iOS).

    In production this would call the respective cloud messaging API.
    For now it logs the intended message so integration tests can
    verify the call chain.
    """

    async def send_order_update(
        self,
        device_token: str,
        order_id: str,
        status: str,
    ) -> dict[str, Any]:
        """Send a push notification about an order status update."""
        logger.info(
            "Push to token=%s — Order %s: %s",
            device_token,
            order_id,
            status,
        )
        return {
            "device_token": device_token,
            "order_id": order_id,
            "status": "sent",
            "title": f"Order {order_id} updated",
            "body": f"Status: {status}",
        }

    async def send_payment_update(
        self,
        device_token: str,
        amount: float,
        status: str,
    ) -> dict[str, Any]:
        """Send a push notification about a payment event."""
        logger.info(
            "Push to token=%s — Amount $%.2f — %s",
            device_token,
            amount,
            status,
        )
        return {
            "device_token": device_token,
            "amount": amount,
            "status": "sent",
            "title": "Payment Update",
            "body": f"Amount: ${amount:.2f} — {status}",
        }
