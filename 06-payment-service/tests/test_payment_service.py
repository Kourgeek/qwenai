"""
Tests for PaymentService business logic.

Covers:
  - create_payment (Stripe & YooMoney)
  - confirm_payment
  - refund_payment
  - webhook handling (Stripe success/failure)
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.payment import Payment, PaymentProvider, PaymentStatus, Refund, RefundStatus
from src.services.payment_service import PaymentService


# ---------------------------------------------------------------------------
# create_payment — happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_payment_stripe(payment_service, fake_user_id, fake_order_id, mock_stripe_client):
    """Should create a PENDING payment and transition to PROCESSING via Stripe."""
    mock_stripe_client.create_payment_intent = AsyncMock(
        return_value={"id": "pi_stripe_001", "status": "requires_payment_method"}
    )

    payment = await payment_service.create_payment(
        order_id=fake_order_id,
        user_id=fake_user_id,
        amount=1000.00,
        currency="RUB",
        provider=PaymentProvider.STRIPE,
    )

    assert payment.order_id == fake_order_id
    assert payment.user_id == fake_user_id
    assert payment.amount == 1000.00
    assert payment.currency == "RUB"
    assert payment.provider == PaymentProvider.STRIPE
    assert payment.provider_payment_id == "pi_stripe_001"

    # Verify Stripe client was called
    mock_stripe_client.create_payment_intent.assert_called_once()


@pytest.mark.asyncio
async def test_create_payment_yoomoney(payment_service, fake_user_id, fake_order_id, mock_yoomoney_client):
    """Should create a PENDING payment and transition to PROCESSING via YooMoney."""
    mock_yoomoney_client.create_payment = AsyncMock(
        return_value={"id": "ym_001", "status": "pending", "confirmation_url": "https://pay.yoomoney.ru/001"}
    )

    payment = await payment_service.create_payment(
        order_id=fake_order_id,
        user_id=fake_user_id,
        amount=500.00,
        currency="RUB",
        provider=PaymentProvider.YOOMONEY,
    )

    assert payment.provider == PaymentProvider.YOOMONEY
    assert payment.provider_payment_id == "ym_001"
    mock_yoomoney_client.create_payment.assert_called_once()


@pytest.mark.asyncio
async def test_create_payment_duplicate_order(payment_service, fake_user_id, fake_order_id, test_session):
    """Should raise ValueError when a payment for the same order already exists."""
    from src.models.payment import Payment, PaymentProvider, PaymentStatus
    from uuid import uuid4

    # Create first payment
    payment1 = Payment(
        id=uuid4(),
        order_id=fake_order_id,
        user_id=fake_user_id,
        amount=100.00,
        currency="RUB",
        status=PaymentStatus.PENDING,
        provider=PaymentProvider.STRIPE,
    )
    test_session.add(payment1)
    await test_session.flush()

    with pytest.raises(ValueError, match=f"Payment already exists for order_id={fake_order_id}"):
        await payment_service.create_payment(
            order_id=fake_order_id,
            user_id=fake_user_id,
            amount=200.00,
            provider=PaymentProvider.STRIPE,
        )


# ---------------------------------------------------------------------------
# confirm_payment
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_confirm_payment_stripe(payment_service, fake_user_id, fake_order_id, mock_stripe_client, test_session):
    """Should confirm a Stripe payment and transition to COMPLETED."""
    # Create a payment first
    mock_stripe_client.create_payment_intent = AsyncMock(
        return_value={"id": "pi_confirm_001", "status": "requires_payment_method"}
    )
    payment = await payment_service.create_payment(
        order_id=fake_order_id,
        user_id=fake_user_id,
        amount=1000.00,
        provider=PaymentProvider.STRIPE,
    )

    # Mock confirm to return "succeeded"
    mock_stripe_client.confirm_payment = AsyncMock(
        return_value={"id": "pi_confirm_001", "status": "succeeded"}
    )

    confirmed = await payment_service.confirm_payment(payment.id)
    assert confirmed.status == PaymentStatus.COMPLETED
    mock_stripe_client.confirm_payment.assert_called_once()
    mock_stripe_client.confirm_payment.assert_called_with("pi_confirm_001")


@pytest.mark.asyncio
async def test_confirm_payment_not_found(payment_service):
    """Should raise ValueError when trying to confirm a non-existent payment."""
    with pytest.raises(ValueError, match="not found"):
        await payment_service.confirm_payment(uuid4())


# ---------------------------------------------------------------------------
# refund_payment
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refund_payment_stripe(payment_service, fake_user_id, fake_order_id, mock_stripe_client, test_session):
    """Should create a refund and mark the payment as REFUNDED."""
    # Create a completed payment
    mock_stripe_client.create_payment_intent = AsyncMock(
        return_value={"id": "pi_refund_001", "status": "requires_payment_method"}
    )
    payment = await payment_service.create_payment(
        order_id=fake_order_id,
        user_id=fake_user_id,
        amount=1000.00,
        provider=PaymentProvider.STRIPE,
    )

    # Simulate the payment being completed (bypass confirm for test simplicity)
    payment.status = PaymentStatus.COMPLETED
    test_session.add(payment)
    await test_session.flush()

    # Mock refund
    mock_stripe_client.refund_payment = AsyncMock(
        return_value={"id": "re_refund_001", "status": "succeeded"}
    )

    refund = await payment_service.refund_payment(
        payment_id=payment.id,
        user_id=fake_user_id,
        amount=500.00,
        reason="requested_by_customer",
    )

    assert refund.amount == 500.00
    assert refund.status == RefundStatus.COMPLETED
    assert refund.provider_refund_id == "re_refund_001"
    mock_stripe_client.refund_payment.assert_called_once()


@pytest.mark.asyncio
async def test_refund_payment_not_completed(payment_service, fake_user_id, fake_order_id, mock_stripe_client):
    """Should raise ValueError when trying to refund a non-completed payment."""
    mock_stripe_client.create_payment_intent = AsyncMock(
        return_value={"id": "pi_norefund_001", "status": "requires_payment_method"}
    )
    payment = await payment_service.create_payment(
        order_id=fake_order_id,
        user_id=fake_user_id,
        amount=1000.00,
        provider=PaymentProvider.STRIPE,
    )

    with pytest.raises(ValueError, match="Cannot refund payment in state"):
        await payment_service.refund_payment(
            payment_id=payment.id,
            user_id=fake_user_id,
            amount=100.00,
        )


# ---------------------------------------------------------------------------
# get_payment
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_payment(payment_service, fake_user_id, fake_order_id, mock_stripe_client, test_session):
    """Should retrieve an existing payment."""
    mock_stripe_client.create_payment_intent = AsyncMock(
        return_value={"id": "pi_get_001", "status": "requires_payment_method"}
    )
    payment = await payment_service.create_payment(
        order_id=fake_order_id,
        user_id=fake_user_id,
        amount=750.00,
        provider=PaymentProvider.STRIPE,
    )

    retrieved = await payment_service.get_payment(payment.id)
    assert retrieved.id == payment.id
    assert retrieved.order_id == fake_order_id


@pytest.mark.asyncio
async def test_get_payment_not_found(payment_service):
    """Should raise ValueError for a non-existent payment."""
    with pytest.raises(ValueError, match="not found"):
        await payment_service.get_payment(uuid4())


# ---------------------------------------------------------------------------
# get_user_payments
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_user_payments(payment_service, fake_user_id, mock_stripe_client, test_session):
    """Should return payments for a specific user."""
    # Create two payments for the same user
    for i in range(2):
        mock_stripe_client.create_payment_intent = AsyncMock(
            return_value={"id": f"pi_list_{i}", "status": "requires_payment_method"}
        )
        await payment_service.create_payment(
            order_id=f"user_order_{i}",
            user_id=fake_user_id,
            amount=100.00,
            provider=PaymentProvider.STRIPE,
        )

    payments = await payment_service.get_user_payments(user_id=fake_user_id)
    assert len(payments) == 2


# ---------------------------------------------------------------------------
# Webhook handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_stripe_webhook_success(payment_service, fake_user_id, fake_order_id, mock_stripe_client, test_session):
    """Should handle a Stripe 'payment_intent.succeeded' webhook."""
    # Create a payment first
    mock_stripe_client.create_payment_intent = AsyncMock(
        return_value={"id": "pi_wh_001", "status": "requires_payment_method"}
    )
    payment = await payment_service.create_payment(
        order_id=fake_order_id,
        user_id=fake_user_id,
        amount=1000.00,
        provider=PaymentProvider.STRIPE,
    )

    # Simulate webhook event
    mock_event = MagicMock()
    mock_event.type = "payment_intent.succeeded"
    mock_event.data.object = {"id": payment.provider_payment_id}

    mock_stripe_client.construct_webhook_event = MagicMock(return_value=mock_event)

    result = await payment_service.handle_webhook(
        provider="stripe",
        payload=b'{"type":"payment_intent.succeeded"}',
        signature="fake_sig",
    )

    assert result["status"] == "ok"
    mock_stripe_client.construct_webhook_event.assert_called_once()


@pytest.mark.asyncio
async def test_handle_stripe_webhook_failure(payment_service, fake_user_id, fake_order_id, mock_stripe_client, test_session):
    """Should handle a Stripe 'payment_intent.payment_failed' webhook."""
    # Create a payment first
    mock_stripe_client.create_payment_intent = AsyncMock(
        return_value={"id": "pi_wh_fail", "status": "requires_payment_method"}
    )
    payment = await payment_service.create_payment(
        order_id=fake_order_id,
        user_id=fake_user_id,
        amount=1000.00,
        provider=PaymentProvider.STRIPE,
    )

    # Simulate failure event
    mock_event = MagicMock()
    mock_event.type = "payment_intent.payment_failed"
    mock_event.data.object = {
        "id": payment.provider_payment_id,
        "last_payment_error": {"message": "Card declined"},
    }

    mock_stripe_client.construct_webhook_event = MagicMock(return_value=mock_event)

    result = await payment_service.handle_webhook(
        provider="stripe",
        payload=b'{"type":"payment_intent.payment_failed"}',
        signature="fake_sig",
    )

    assert result["status"] == "ok"


@pytest.mark.asyncio
async def test_handle_yoomoney_webhook(payment_service, fake_user_id, fake_order_id, mock_yoomoney_client, test_session):
    """Should handle a YooMoney webhook."""
    # Create a YooMoney payment
    mock_yoomoney_client.create_payment = AsyncMock(
        return_value={"id": "ym_wh_001", "status": "pending", "confirmation_url": "https://pay.yoomoney.ru/wh"}
    )
    payment = await payment_service.create_payment(
        order_id=fake_order_id,
        user_id=fake_user_id,
        amount=500.00,
        provider=PaymentProvider.YOOMONEY,
    )

    # YooMoney webhook signature verification
    mock_yoomoney_client.verify_webhook_signature = MagicMock(return_value=True)

    import json

    payload = json.dumps({
        "event_type": "payment_succeeded",
        "invoice": {"invoice_id": fake_order_id},
    }).encode()

    result = await payment_service.handle_webhook(
        provider="yoomoney",
        payload=payload,
        signature="fake_checksum",
    )

    assert result["status"] == "ok"
