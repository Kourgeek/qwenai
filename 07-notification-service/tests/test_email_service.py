"""Tests for the EmailService — welcome, order confirmation, and payment receipt."""

import pytest
from unittest.mock import AsyncMock, patch

from src.services.email_service import EmailService


@pytest.fixture
def email_service() -> EmailService:
    return EmailService()


# ------------------------------------------------------------------
# send_welcome_email
# ------------------------------------------------------------------
class TestSendWelcomeEmail:
    @pytest.mark.asyncio
    async def test_sends_email_to_recipient(self, email_service, mock_smtp):
        """Verify that send_welcome_email calls aiosmtplib.send."""
        await email_service.send_welcome_email("user@example.com", "Alice")

        mock_smtp.assert_called_once()
        call_args = mock_smtp.call_args
        # The first positional arg is the EmailMessage object
        msg = call_args[0][0]
        assert msg["To"] == "user@example.com"
        assert "Welcome to HyperScale Marketplace" in msg["Subject"]
        assert "Alice" in msg.get_content()

    @pytest.mark.asyncio
    async def test_raises_on_smtp_failure(self, email_service, mock_smtp):
        """Verify that SMTP errors propagate."""
        mock_smtp.side_effect = ConnectionRefusedError("connection refused")
        with pytest.raises(ConnectionRefusedError):
            await email_service.send_welcome_email("fail@example.com", "Bob")


# ------------------------------------------------------------------
# send_order_confirmation
# ------------------------------------------------------------------
class TestSendOrderConfirmation:
    @pytest.mark.asyncio
    async def test_sends_order_confirmation(self, email_service, mock_smtp):
        """Verify order confirmation email content."""
        items = [
            {"name": "Widget A", "qty": 2, "price": 19.99},
            {"name": "Widget B", "qty": 1, "price": 49.99},
        ]
        await email_service.send_order_confirmation(
            order_id="ORD-12345",
            user_email="buyer@example.com",
            items=items,
            total=89.97,
        )

        mock_smtp.assert_called_once()
        msg = mock_smtp.call_args[0][0]
        assert msg["To"] == "buyer@example.com"
        assert "ORD-12345" in msg["Subject"]
        assert "Widget A" in msg.get_content()
        assert "Widget B" in msg.get_content()
        assert "$89.97" in msg.get_content()

    @pytest.mark.asyncio
    async def test_raises_on_smtp_failure(self, email_service, mock_smtp):
        """Verify that SMTP errors propagate."""
        mock_smtp.side_effect = ConnectionRefusedError("connection refused")
        with pytest.raises(ConnectionRefusedError):
            await email_service.send_order_confirmation(
                order_id="ORD-99999",
                user_email="buyer@example.com",
                items=[],
                total=0.0,
            )


# ------------------------------------------------------------------
# send_payment_receipt
# ------------------------------------------------------------------
class TestSendPaymentReceipt:
    @pytest.mark.asyncio
    async def test_sends_payment_receipt(self, email_service, mock_smtp):
        """Verify payment receipt email content."""
        await email_service.send_payment_receipt(
            payment_id="PAY-67890",
            user_email="buyer@example.com",
            amount=150.00,
        )

        mock_smtp.assert_called_once()
        msg = mock_smtp.call_args[0][0]
        assert msg["To"] == "buyer@example.com"
        assert "PAY-67890" in msg["Subject"]
        assert "$150.00" in msg.get_content()
        # Should include a UTC date
        assert "Date:" in msg.get_content()

    @pytest.mark.asyncio
    async def test_raises_on_smtp_failure(self, email_service, mock_smtp):
        """Verify that SMTP errors propagate."""
        mock_smtp.side_effect = ConnectionRefusedError("connection refused")
        with pytest.raises(ConnectionRefusedError):
            await email_service.send_payment_receipt(
                payment_id="PAY-00001",
                user_email="buyer@example.com",
                amount=10.00,
            )
