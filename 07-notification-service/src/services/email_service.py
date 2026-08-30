"""Async email service using aiosmtplib."""

import logging
from datetime import datetime, timezone

import aiosmtplib
from aiosmtplib import SMTP
from email.message import EmailMessage

from src.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Sends transactional emails via SMTP (async)."""

    async def send_welcome_email(self, user_email: str, user_name: str) -> None:
        """Send a welcome email to a newly registered user."""
        subject = "Welcome to HyperScale Marketplace"
        body = self._render_welcome(user_name)
        await self._send_email(user_email, subject, body)

    async def send_order_confirmation(
        self,
        order_id: str,
        user_email: str,
        items: list[dict],
        total: float,
    ) -> None:
        """Send an order confirmation email."""
        subject = f"Order Confirmation — {order_id}"
        body = self._render_order_confirmation(order_id, items, total)
        await self._send_email(user_email, subject, body)

    async def send_payment_receipt(
        self,
        payment_id: str,
        user_email: str,
        amount: float,
    ) -> None:
        """Send a payment receipt email."""
        subject = f"Payment Receipt — {payment_id}"
        body = self._render_payment_receipt(payment_id, amount)
        await self._send_email(user_email, subject, body)

    async def send_order_status_update(
        self,
        order_id: str,
        user_email: str,
        status: str,
    ) -> None:
        """Send an order status update email."""
        subject = f"Order Status Update — {order_id}"
        body = self._render_order_status_update(order_id, status)
        await self._send_email(user_email, subject, body)

    async def send_refund_notification(
        self,
        payment_id: str,
        user_email: str,
        amount: float,
    ) -> None:
        """Send a refund notification email."""
        subject = f"Refund Notification — {payment_id}"
        body = self._render_refund_notification(payment_id, amount)
        await self._send_email(user_email, subject, body)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _send_email(
        self,
        to: str,
        subject: str,
        body: str,
    ) -> None:
        msg = EmailMessage()
        msg["From"] = settings.mail_user
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.mail_host,
                port=settings.mail_port,
                username=settings.mail_user if settings.mail_user else None,
                password=settings.mail_password if settings.mail_password else None,
                start_tls=True,
            )
            logger.info("Email sent to %s", to)
        except Exception:
            logger.exception("Failed to send email to %s", to)
            raise

    # ------------------------------------------------------------------
    # Template renderers
    # ------------------------------------------------------------------
    def _render_welcome(self, name: str) -> str:
        return f"""\
Dear {name},

Welcome to HyperScale Marketplace! We are glad to have you on board.

Best regards,
The HyperScale Team
"""

    def _render_order_confirmation(
        self, order_id: str, items: list[dict], total: float
    ) -> str:
        items_html = "\n".join(
            f"  - {item.get('name', 'Item')} x{item.get('qty', 1)} — ${item.get('price', 0):.2f}"
            for item in items
        )
        return f"""\
Dear Customer,

Thank you for your order!

Order ID: {order_id}
Items:
{items_html}

Total: ${total:.2f}

Best regards,
The HyperScale Team
"""

    def _render_payment_receipt(self, payment_id: str, amount: float) -> str:
        return f"""\
Dear Customer,

Your payment has been processed successfully.

Payment ID: {payment_id}
Amount: ${amount:.2f}
Date: {datetime.now(timezone.utc).isoformat()}

Best regards,
The HyperScale Team
"""

    def _render_order_status_update(self, order_id: str, status: str) -> str:
        return f"""\
Dear Customer,

Your order status has been updated.

Order ID: {order_id}
Status: {status}

Best regards,
The HyperScale Team
"""

    def _render_refund_notification(self, payment_id: str, amount: float) -> str:
        return f"""\
Dear Customer,

A refund has been processed for your order.

Payment ID: {payment_id}
Refund Amount: ${amount:.2f}

The refund will appear in your account within 5-7 business days.

Best regards,
The HyperScale Team
"""
