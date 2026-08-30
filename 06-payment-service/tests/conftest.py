"""
Shared test fixtures for the Payment Service test suite.

Provides:
  - Async database session (in-memory SQLite fallback for tests)
  - Mocked Stripe and YooMoney clients
  - Kafka producer mock
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import Settings
from src.models.payment import Base
from src.repositories.payment_repository import PaymentRepository
from src.repositories.payment_method_repository import PaymentMethodRepository
from src.repositories.refund_repository import RefundRepository
from src.services.payment_service import PaymentService
from src.stripe_client.stripe_client import StripeClient
from src.stripe_client.yoomoney_client import YooMoneyClient
from src.kafka.producer import PaymentKafkaProducer


# ---------------------------------------------------------------------------
# Test settings (override defaults)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Use an in-memory SQLite database for tests."""
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine(test_db_url):
    """Create a test engine with tables."""
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(test_db_url, echo=False)

    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    import asyncio

    asyncio.run(_setup())
    return engine


@pytest.fixture
async def test_session(test_engine):
    """Provide a fresh async session per test."""
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# Mock clients
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_stripe_client():
    """Mock StripeClient with async methods."""
    mock = AsyncMock(spec=StripeClient)
    mock.create_payment_intent = AsyncMock(return_value={"id": "pi_mock123", "status": "requires_payment_method"})
    mock.confirm_payment = AsyncMock(return_value={"id": "pi_mock123", "status": "succeeded"})
    mock.refund_payment = AsyncMock(return_value={"id": "re_mock123", "status": "succeeded"})
    mock.construct_webhook_event = MagicMock()
    mock.get_payment_intent = AsyncMock(return_value={"id": "pi_mock123", "status": "succeeded"})
    return mock


@pytest.fixture
def mock_yoomoney_client():
    """Mock YooMoneyClient with async methods."""
    mock = AsyncMock(spec=YooMoneyClient)
    mock.create_payment = AsyncMock(
        return_value={"id": "ym_pay_123", "status": "pending", "confirmation_url": "https://pay.yoomoney.ru/123"}
    )
    mock.confirm_payment = AsyncMock(return_value={"id": "ym_pay_123", "status": "confirmed"})
    mock.refund_payment = AsyncMock(return_value={"operation_id": "ym_ref_456", "status": "succeeded"})
    mock.verify_webhook_signature = MagicMock(return_value=True)
    return mock


@pytest.fixture
def mock_kafka_producer():
    """Mock PaymentKafkaProducer with async methods."""
    mock = AsyncMock(spec=PaymentKafkaProducer)
    mock.publish = AsyncMock()
    mock.publish_payment_completed = AsyncMock()
    mock.publish_payment_failed = AsyncMock()
    mock.publish_refund_completed = AsyncMock()
    return mock


# ---------------------------------------------------------------------------
# PaymentService fixture
# ---------------------------------------------------------------------------


@pytest.fixture
async def payment_service(test_session, mock_stripe_client, mock_yoomoney_client, mock_kafka_producer):
    """Construct a PaymentService with mocked dependencies."""
    return PaymentService(
        session=test_session,
        stripe_client=mock_stripe_client,
        yoomoney_client=mock_yoomoney_client,
        kafka_producer=mock_kafka_producer,
    )


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_user_id():
    return uuid4()


@pytest.fixture
def fake_order_id():
    return f"order-{uuid4().hex[:8]}"
