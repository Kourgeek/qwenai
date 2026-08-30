"""Tests for UserService (get_user / update_user)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.services.user_service import UserService


@pytest.mark.asyncio
async def test_get_user_returns_dto(db_session: AsyncSession, inserted_user):
    """get_user should return a UserDTO with correct fields."""
    service = UserService(db_session)
    dto = await service.get_user(inserted_user.id)

    assert dto is not None
    assert dto.id == inserted_user.id
    assert dto.email == inserted_user.email
    assert dto.username == inserted_user.username
    assert dto.display_name == "Test User"
    assert dto.is_active is True


@pytest.mark.asyncio
async def test_get_user_not_found(db_session: AsyncSession):
    """get_user should return None for a non-existent UUID."""
    import uuid

    service = UserService(db_session)
    dto = await service.get_user(uuid.uuid4())
    assert dto is None


@pytest.mark.asyncio
async def test_update_user_changes_email(db_session: AsyncSession, inserted_user):
    """update_user should change the email and return the updated DTO."""
    service = UserService(db_session)
    new_email = "updated@example.com"
    dto = await service.update_user(inserted_user.id, email=new_email)

    assert dto.email == new_email

    # Verify persistence
    fresh_user: User = await db_session.get(User, inserted_user.id)
    assert fresh_user.email == new_email


@pytest.mark.asyncio
async def test_update_user_changes_username(db_session: AsyncSession, inserted_user):
    service = UserService(db_session)
    dto = await service.update_user(inserted_user.id, username="newuser")
    assert dto.username == "newuser"


@pytest.mark.asyncio
async def test_update_user_not_found(db_session: AsyncSession):
    import uuid

    service = UserService(db_session)
    with pytest.raises(ValueError, match="not found"):
        await service.update_user(uuid.uuid4(), email="x@x.com")


@pytest.mark.asyncio
async def test_update_user_duplicate_email(db_session: AsyncSession):
    """Should raise when the new email is already in use."""
    from src.repositories.user_repository import UserRepository

    user_a = User(email="a@example.com", username="user_a")
    user_b = User(email="b@example.com", username="user_b")
    db_session.add_all([user_a, user_b])
    await db_session.commit()
    await db_session.refresh(user_a)
    await db_session.refresh(user_b)

    service = UserService(db_session)
    with pytest.raises(ValueError, match="already in use"):
        await service.update_user(user_b.id, email="a@example.com")
