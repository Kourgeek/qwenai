"""Tests for OrderService business logic."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.order_service import OrderService, VALID_STATUSES
from src.kafka.publisher import OrderKafkaPublisher


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def order_service(mock_kafka_publisher: AsyncMock) -> OrderService:
    return OrderService(kafka_publisher=mock_kafka_publisher)


@pytest.fixture
def mock_session() -> MagicMock:
    session = MagicMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.get = AsyncMock()
    session.close = AsyncMock()
    return session


# ── create_order ──────────────────────────────────────────────────────────


class TestCreateOrder:
    @pytest.mark.asyncio
    async def test_creates_order_with_valid_cart(
        self,
        order_service: OrderService,
        mock_session: MagicMock,
        mock_cart_client: AsyncMock,
        mock_catalog_client: AsyncMock,
        mock_kafka_publisher: AsyncMock,
    ):
        mock_cart_client.return_value = {
            "items": [{"product_id": 1, "quantity": 2}],
            "total": 59.98,
            "currency": "USD",
        }

        with patch("src.services.order_service.get_cart", mock_cart_client):
            with patch("src.services.order_service.get_product", mock_catalog_client):
                # Simulate repo create returning a persisted Order-like object
                mock_session.add = MagicMock()
                mock_session.flush = AsyncMock()
                mock_session.refresh = AsyncMock()

                async def fake_refresh(obj):
                    obj.id = 42
                    obj.status = "PENDING"
                    obj.total_amount = 59.98
                    obj.currency = "USD"
                    obj.created_at = None
                    obj.updated_at = None
                    obj.completed_at = None
                    obj.cancelled_at = None
                    obj.items = []
                    return obj

                mock_session.refresh.side_effect = fake_refresh

                order = await order_service.create_order(
                    session=mock_session,
                    user_id=100,
                    cart_id=999,
                )

                assert order is not None
                assert order.id == 42
                assert order.status == "PENDING"
                assert order.total_amount == 59.98

                # Verify Kafka event was published
                mock_kafka_publisher.publish_order_created.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_on_empty_cart(
        self,
        order_service: OrderService,
        mock_session: MagicMock,
        mock_cart_client: AsyncMock,
    ):
        mock_cart_client.return_value = {"items": [], "total": 0.0, "currency": "USD"}

        with patch("src.services.order_service.get_cart", mock_cart_client):
            with pytest.raises(ValueError, match="Cart is empty"):
                await order_service.create_order(
                    session=mock_session,
                    user_id=100,
                    cart_id=999,
                )


# ── get_order ─────────────────────────────────────────────────────────────


class TestGetOrder:
    @pytest.mark.asyncio
    async def test_returns_order_when_found(
        self,
        order_service: OrderService,
        mock_session: MagicMock,
    ):
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "PENDING"
        mock_order.total_amount = 10.0
        mock_order.currency = "EUR"
        mock_session.get = AsyncMock(return_value=mock_order)

        # Patch the repo to use our mock session
        from src.repositories.order_repository import OrderRepository

        repo = OrderRepository(mock_session)
        repo.get_by_id = AsyncMock(return_value=mock_order)
        order_service._get_order_repo = AsyncMock(return_value=repo)

        order = await order_service.get_order(mock_session, order_id=1)
        assert order is not None
        assert order.id == 1
        assert order.status == "PENDING"

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(
        self,
        order_service: OrderService,
        mock_session: MagicMock,
    ):
        from src.repositories.order_repository import OrderRepository

        repo = OrderRepository(mock_session)
        repo.get_by_id = AsyncMock(return_value=None)
        order_service._get_order_repo = AsyncMock(return_value=repo)

        order = await order_service.get_order(mock_session, order_id=999)
        assert order is None


# ── cancel_order ──────────────────────────────────────────────────────────


class TestCancelOrder:
    @pytest.mark.asyncio
    async def test_cancels_pending_order(
        self,
        order_service: OrderService,
        mock_session: MagicMock,
        mock_kafka_publisher: AsyncMock,
    ):
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.user_id = 100
        mock_order.status = "PENDING"
        mock_order.cancelled_at = None
        mock_order.cancelled_by = None
        mock_order.cancellation_reason = None
        mock_session.get = AsyncMock(return_value=mock_order)

        from src.repositories.order_repository import OrderRepository

        repo = OrderRepository(mock_session)
        repo.get_by_id = AsyncMock(return_value=mock_order)
        order_service._get_order_repo = AsyncMock(return_value=repo)

        result = await order_service.cancel_order(
            mock_session, order_id=1, user_id=100, reason="Changed mind"
        )

        assert result.status == "CANCELLED"
        assert result.cancelled_by == 100
        assert result.cancellation_reason == "Changed mind"
        mock_kafka_publisher.publish_order_status_changed.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_for_unauthorized_user(
        self,
        order_service: OrderService,
        mock_session: MagicMock,
    ):
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.user_id = 200  # different user
        mock_order.status = "PENDING"
        mock_session.get = AsyncMock(return_value=mock_order)

        from src.repositories.order_repository import OrderRepository

        repo = OrderRepository(mock_session)
        repo.get_by_id = AsyncMock(return_value=mock_order)
        order_service._get_order_repo = AsyncMock(return_value=repo)

        with pytest.raises(PermissionError, match="does not own"):
            await order_service.cancel_order(
                mock_session, order_id=1, user_id=100
            )

    @pytest.mark.asyncio
    async def test_raises_for_shipped_order(
        self,
        order_service: OrderService,
        mock_session: MagicMock,
    ):
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.user_id = 100
        mock_order.status = "SHIPPED"
        mock_session.get = AsyncMock(return_value=mock_order)

        from src.repositories.order_repository import OrderRepository

        repo = OrderRepository(mock_session)
        repo.get_by_id = AsyncMock(return_value=mock_order)
        order_service._get_order_repo = AsyncMock(return_value=repo)

        with pytest.raises(ValueError, match="Cannot cancel"):
            await order_service.cancel_order(
                mock_session, order_id=1, user_id=100
            )


# ── update_order_status ───────────────────────────────────────────────────


class TestUpdateOrderStatus:
    @pytest.mark.asyncio
    async def test_transitions_pending_to_confirmed(
        self,
        order_service: OrderService,
        mock_session: MagicMock,
        mock_kafka_publisher: AsyncMock,
    ):
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "PENDING"
        mock_session.get = AsyncMock(return_value=mock_order)

        from src.repositories.order_repository import OrderRepository

        repo = OrderRepository(mock_session)
        repo.get_by_id = AsyncMock(return_value=mock_order)
        order_service._get_order_repo = AsyncMock(return_value=repo)

        result = await order_service.update_order_status(
            mock_session, order_id=1, new_status="CONFIRMED"
        )

        assert result.status == "CONFIRMED"
        mock_kafka_publisher.publish_order_status_changed.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_on_invalid_transition(
        self,
        order_service: OrderService,
        mock_session: MagicMock,
    ):
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "PENDING"
        mock_session.get = AsyncMock(return_value=mock_order)

        from src.repositories.order_repository import OrderRepository

        repo = OrderRepository(mock_session)
        repo.get_by_id = AsyncMock(return_value=mock_order)
        order_service._get_order_repo = AsyncMock(return_value=repo)

        with pytest.raises(ValueError, match="Cannot transition"):
            await order_service.update_order_status(
                mock_session, order_id=1, new_status="DELIVERED"
            )

    @pytest.mark.asyncio
    async def test_raises_on_invalid_status_value(
        self,
        order_service: OrderService,
        mock_session: MagicMock,
    ):
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "PENDING"
        mock_session.get = AsyncMock(return_value=mock_order)

        from src.repositories.order_repository import OrderRepository

        repo = OrderRepository(mock_session)
        repo.get_by_id = AsyncMock(return_value=mock_order)
        order_service._get_order_repo = AsyncMock(return_value=repo)

        with pytest.raises(ValueError, match="Invalid status"):
            await order_service.update_order_status(
                mock_session, order_id=1, new_status="INVALID"
            )
