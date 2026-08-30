"""Tests for CartService business logic."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.cart_service import CartService


@pytest.mark.asyncio
async def test_add_item(mock_catalog_get_product, mock_redis, user_id, product_id):
    """Adding a valid product calls catalog and persists to Redis."""
    svc = CartService(redis_mock := MagicMock())
    svc.get_cart = AsyncMock(return_value={"user_id": user_id, "items": [], "total": 0.0})
    svc._redis = mock_redis

    result = await svc.add_item(user_id, product_id, 2)

    mock_redis.add_item.assert_called_once_with(
        user_id=user_id,
        product_id=product_id,
        product_name="Test Product",
        unit_price=9.99,
        quantity=2,
    )
    assert result["total"] == 0.0  # get_cart mocked to return empty


@pytest.mark.asyncio
async def test_add_item_rejects_zero_quantity():
    """Quantity <= 0 must raise ValueError."""
    svc = CartService()
    with pytest.raises(ValueError, match="greater than 0"):
        await svc.add_item("user-1", "p-1", 0)


@pytest.mark.asyncio
async def test_add_item_rejects_negative_quantity():
    """Negative quantity must raise ValueError."""
    svc = CartService()
    with pytest.raises(ValueError, match="greater than 0"):
        await svc.add_item("user-1", "p-1", -5)


@pytest.mark.asyncio
async def test_update_item(mock_redis, user_id, product_id):
    """Updating quantity calls redis and returns fresh cart."""
    svc = CartService(redis_mock := MagicMock())
    svc.get_cart = AsyncMock(return_value={"user_id": user_id, "items": [], "total": 0.0})
    svc._redis = mock_redis

    result = await svc.update_item(user_id, product_id, 5)

    mock_redis.update_item.assert_called_once_with(
        user_id=user_id,
        product_id=product_id,
        quantity=5,
    )
    assert result["total"] == 0.0


@pytest.mark.asyncio
async def test_update_item_zero_calls_remove(mock_redis, user_id, product_id):
    """Quantity <= 0 delegates to remove_item."""
    svc = CartService(redis_mock := MagicMock())
    svc.get_cart = AsyncMock(return_value={"user_id": user_id, "items": [], "total": 0.0})
    svc._redis = mock_redis

    await svc.update_item(user_id, product_id, 0)

    mock_redis.remove_item.assert_called_once_with(user_id=user_id, product_id=product_id)


@pytest.mark.asyncio
async def test_remove_item(mock_redis, user_id, product_id, sample_cart):
    """Removing an existing item deletes it from Redis."""
    svc = CartService(redis_mock := MagicMock())
    svc.get_cart = AsyncMock(return_value=sample_cart)
    svc._redis = mock_redis

    result = await svc.remove_item(user_id, product_id)

    mock_redis.remove_item.assert_called_once_with(user_id=user_id, product_id=product_id)
    assert result["total"] == 0.0


@pytest.mark.asyncio
async def test_remove_item_not_in_cart(mock_redis, user_id):
    """Removing a product not in cart raises KeyError."""
    svc = CartService(redis_mock := MagicMock())
    svc.get_cart = AsyncMock(return_value={"user_id": user_id, "items": [], "total": 0.0})
    svc._redis = mock_redis

    with pytest.raises(KeyError, match="not in cart"):
        await svc.remove_item(user_id, "nonexistent")


@pytest.mark.asyncio
async def test_clear_cart(mock_redis, user_id, sample_cart):
    """Clearing the cart deletes the Redis key and returns empty cart."""
    svc = CartService(redis_mock := MagicMock())
    svc.get_cart = AsyncMock(return_value=sample_cart)
    svc._redis = mock_redis

    result = await svc.clear_cart(user_id)

    mock_redis.clear_cart.assert_called_once_with(user_id)
    assert result == {"user_id": user_id, "items": [], "total": 0.0}


@pytest.mark.asyncio
async def test_clear_cart_empty_cart(mock_redis, user_id):
    """Clearing an empty cart raises KeyError."""
    svc = CartService(redis_mock := MagicMock())
    svc.get_cart = AsyncMock(return_value=None)
    svc._redis = mock_redis

    with pytest.raises(KeyError, match="does not exist"):
        await svc.clear_cart(user_id)


@pytest.mark.asyncio
async def test_save_for_later(mock_redis, user_id, product_id, sample_cart):
    """Moving an item to saved-for-later works end-to-end."""
    svc = CartService(redis_mock := MagicMock())
    svc.get_cart = AsyncMock(return_value=sample_cart)
    svc._redis = mock_redis

    result = await svc.save_for_later(user_id, product_id)

    mock_redis.save_for_later.assert_called_once_with(
        user_id=user_id,
        product_id=product_id,
        product_name="Widget A",
        unit_price=10.0,
        quantity=2,
    )
    assert result["total"] == 0.0


@pytest.mark.asyncio
async def test_save_for_later_product_not_in_cart(mock_redis, user_id):
    """Saving a product not in cart raises KeyError."""
    svc = CartService(redis_mock := MagicMock())
    svc.get_cart = AsyncMock(return_value={"user_id": user_id, "items": [], "total": 0.0})
    svc._redis = mock_redis

    with pytest.raises(KeyError, match="not in cart"):
        await svc.save_for_later(user_id, "nonexistent")


@pytest.mark.asyncio
async def test_move_to_cart(mock_redis, user_id, product_id):
    """Moving an item from saved list back to cart works."""
    svc = CartService(redis_mock := MagicMock())
    svc.get_cart = AsyncMock(return_value={"user_id": user_id, "items": [], "total": 0.0})
    svc._redis = mock_redis

    result = await svc.move_to_cart(user_id, product_id)

    mock_redis.move_to_cart.assert_called_once_with(user_id=user_id, product_id=product_id)
    assert result["total"] == 0.0


@pytest.mark.asyncio
async def test_get_cart_empty_returns_default(mock_redis, user_id):
    """When Redis returns None, an empty cart dict is returned."""
    svc = CartService(redis_mock := MagicMock())
    svc._redis = mock_redis
    mock_redis.get_cart = AsyncMock(return_value=None)

    result = await svc.get_cart(user_id)

    assert result == {"user_id": user_id, "items": [], "total": 0.0}
    mock_redis.get_cart.assert_called_once_with(user_id)
