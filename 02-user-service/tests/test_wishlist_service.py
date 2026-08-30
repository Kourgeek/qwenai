"""Tests for WishlistService (add / get / remove)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.services.wishlist_service import WishlistService


@pytest.fixture()
async def test_user(db_session: AsyncSession):
    """Create a user so wishlist items can be attached."""
    user = User(email="wish_test@example.com", username="wish_test")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ── add_to_wishlist ────────────────────────────────────────────
@pytest.mark.asyncio
async def test_add_to_wishlist_creates_item(db_session: AsyncSession, test_user, product_id):
    service = WishlistService(db_session)
    item = await service.add_to_wishlist(test_user.id, product_id)
    assert item.id is not None
    assert item.user_id == test_user.id
    assert item.product_id == product_id


@pytest.mark.asyncio
async def test_add_duplicate_raises(db_session: AsyncSession, test_user, product_id):
    service = WishlistService(db_session)
    await service.add_to_wishlist(test_user.id, product_id)
    with pytest.raises(ValueError, match="already in"):
        await service.add_to_wishlist(test_user.id, product_id)


# ── get_wishlist ───────────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_wishlist_returns_items(db_session: AsyncSession, test_user, product_id):
    service = WishlistService(db_session)
    await service.add_to_wishlist(test_user.id, product_id)
    items = await service.get_wishlist(test_user.id)
    assert len(items) == 1
    assert items[0].product_id == product_id


# ── remove_from_wishlist ───────────────────────────────────────
@pytest.mark.asyncio
async def test_remove_from_wishlist(db_session: AsyncSession, test_user, product_id):
    service = WishlistService(db_session)
    await service.add_to_wishlist(test_user.id, product_id)
    removed = await service.remove_from_wishlist(test_user.id, product_id)
    assert removed is True

    items = await service.get_wishlist(test_user.id)
    assert len(items) == 0


@pytest.mark.asyncio
async def test_remove_nonexistent_returns_false(db_session: AsyncSession, test_user):
    service = WishlistService(db_session)
    removed = await service.remove_from_wishlist(test_user.id, "nonexistent")
    assert removed is False
