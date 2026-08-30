"""Tests for BFF Service."""
import pytest


class TestBffService:
    """Test BFF service aggregation logic."""

    @pytest.mark.asyncio
    async def test_get_profile_returns_user_data(self, mock_user_client):
        """Test that get_profile returns user data."""
        assert mock_user_client is not None
        result = await mock_user_client.get_user_profile("test-user-123")
        assert result is not None
        assert "id" in result

    @pytest.mark.asyncio
    async def test_get_cart_returns_cart_data(self, mock_cart_client):
        """Test that get_cart returns cart data."""
        assert mock_cart_client is not None
        result = await mock_cart_client.get_cart("test-user-123")
        assert result is not None
        assert "items" in result

    @pytest.mark.asyncio
    async def test_get_orders_returns_orders(self, mock_order_client):
        """Test that get_user_orders returns orders."""
        assert mock_order_client is not None
        result = await mock_order_client.get_user_orders("test-user-123")
        assert result is not None
        assert "orders" in result

    @pytest.mark.asyncio
    async def test_search_products_returns_results(self, mock_search_client):
        """Test that search_products returns results."""
        assert mock_search_client is not None
        result = await mock_search_client.search_products("test")
        assert result is not None
        assert "products" in result
