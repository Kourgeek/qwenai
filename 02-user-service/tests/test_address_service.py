"""Tests for AddressService (add / update / delete / list / set_default)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.services.address_service import AddressService


@pytest.fixture()
async def test_user(db_session: AsyncSession):
    """Create a user so addresses can be attached."""
    user = User(email="addr_test@example.com", username="addr_test")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ── add_address ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_add_address_creates_row(db_session: AsyncSession, test_user):
    service = AddressService(db_session)
    address = await service.add_address(
        test_user.id,
        street="123 Main St",
        city="Moscow",
        postal_code="101000",
        country="RU",
    )
    assert address.id is not None
    assert address.street == "123 Main St"
    assert address.city == "Moscow"
    assert address.user_id == test_user.id


@pytest.mark.asyncio
async def test_add_default_address_clears_others(db_session: AsyncSession, test_user):
    service = AddressService(db_session)

    addr1 = await service.add_address(test_user.id, street="A", city="A", postal_code="1")
    addr2 = await service.add_address(test_user.id, street="B", city="B", postal_code="2", is_default=True)

    assert addr1.is_default is False
    assert addr2.is_default is True


# ── update_address ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_update_address_changes_field(db_session: AsyncSession, test_user):
    service = AddressService(db_session)
    address = await service.add_address(test_user.id, street="Old", city="Old", postal_code="0")
    updated = await service.update_address(address.id, street="New")
    assert updated.street == "New"


@pytest.mark.asyncio
async def test_update_address_not_found(db_session: AsyncSession):
    import uuid

    service = AddressService(db_session)
    with pytest.raises(ValueError, match="not found"):
        await service.update_address(uuid.uuid4(), street="x")


# ── delete_address ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_delete_address(db_session: AsyncSession, test_user):
    service = AddressService(db_session)
    address = await service.add_address(test_user.id, street="Del", city="Del", postal_code="0")
    await service.delete_address(address.id)

    # Should raise on re-fetch
    with pytest.raises(ValueError, match="not found"):
        await service.delete_address(address.id)


# ── list_addresses ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_addresses_returns_all(db_session: AsyncSession, test_user):
    service = AddressService(db_session)
    await service.add_address(test_user.id, street="1", city="1", postal_code="0")
    await service.add_address(test_user.id, street="2", city="2", postal_code="0")

    addresses = await service.list_addresses(test_user.id)
    assert len(addresses) == 2


# ── set_default_address ────────────────────────────────────────
@pytest.mark.asyncio
async def test_set_default_address(db_session: AsyncSession, test_user):
    service = AddressService(db_session)
    addr1 = await service.add_address(test_user.id, street="A", city="A", postal_code="0")
    addr2 = await service.add_address(test_user.id, street="B", city="B", postal_code="0")

    await service.set_default_address(addr2.id)
    assert addr2.is_default is True
    assert addr1.is_default is False
