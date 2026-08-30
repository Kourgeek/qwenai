"""Shared pytest fixtures for the Notification Service test suite."""

import asyncio
from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest


# ------------------------------------------------------------------
# Kafka consumer mock
# ------------------------------------------------------------------
@pytest.fixture
def mock_kafka_consumer() -> AsyncMock:
    """Return a mock OrderKafkaConsumer with async callback methods."""
    mock = AsyncMock()
    mock.consume_order_created = AsyncMock()
    mock.consume_payment_completed = AsyncMock()
    mock.consume_refund_completed = AsyncMock()
    mock.setup = MagicMock()
    mock.start = MagicMock()
    mock.stop = AsyncMock()
    return mock


# ------------------------------------------------------------------
# Email service mock
# ------------------------------------------------------------------
@pytest.fixture
def mock_email_service() -> AsyncMock:
    """Return a mock EmailService with async send methods."""
    mock = AsyncMock()
    mock.send_welcome_email = AsyncMock()
    mock.send_order_confirmation = AsyncMock()
    mock.send_payment_receipt = AsyncMock()
    mock.send_order_status_update = AsyncMock()
    mock.send_refund_notification = AsyncMock()
    mock._send_email = AsyncMock()
    return mock


# ------------------------------------------------------------------
# Mail client mock (aiosmtplib replacement)
# ------------------------------------------------------------------
@pytest.fixture
def mock_smtp() -> AsyncMock:
    """Mock aiosmtplib.send to avoid real SMTP calls."""
    with __import__("unittest.mock").mock.patch(
        "src.services.email_service.aiosmtplib.send",
        new_callable=AsyncMock,
    ) as mock_send:
        mock_send.return_value = None
        yield mock_send


# ------------------------------------------------------------------
# gRPC servicer mock
# ------------------------------------------------------------------
@pytest.fixture
def mock_grpc_servicer() -> AsyncMock:
    """Return a mock gRPC NotificationServiceServicer."""
    mock = AsyncMock()
    mock._history = []
    mock._stats = {
        "email_sent": 0,
        "sms_sent": 0,
        "push_sent": 0,
        "email_failed": 0,
        "sms_failed": 0,
        "push_failed": 0,
    }
    return mock


# ------------------------------------------------------------------
# Event loop scope (pytest-asyncio compatibility)
# ------------------------------------------------------------------
@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
