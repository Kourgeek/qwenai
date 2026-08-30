"""Business logic for User operations."""

import logging
import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


@dataclass
class UserDTO:
    """Plain-data transfer object for User."""

    id: uuid.UUID
    email: str
    username: str
    display_name: str | None = None
    phone_number: str | None = None
    avatar_url: str | None = None
    is_active: bool = True


class UserService:
    """Orchestrates user-level business logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = UserRepository(session)

    async def get_user(self, user_id: uuid.UUID) -> UserDTO | None:
        """Return a DTO for the user with *user_id*, or ``None``."""
        user = await self._repo.get_by_id(user_id)
        if user is None:
            return None
        return UserDTO(
            id=user.id,
            email=user.email,
            username=user.username,
            display_name=user.display_name,
            phone_number=user.phone_number,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
        )

    async def update_user(
        self,
        user_id: uuid.UUID,
        *,
        email: str | None = None,
        username: str | None = None,
        display_name: str | None = None,
        phone_number: str | None = None,
        avatar_url: str | None = None,
        is_active: bool | None = None,
    ) -> UserDTO:
        """Update a user and return the new DTO.

        Raises ``ValueError`` when the user does not exist or a
        uniqueness constraint would be violated.
        """
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")

        # Pre-check uniqueness when email/username change.
        if email is not None and email != user.email:
            existing = await self._repo.get_by_email(email)
            if existing and existing.id != user_id:
                raise ValueError(f"Email {email} is already in use")

        if username is not None and username != user.username:
            existing = await self._repo.get_by_username(username)
            if existing and existing.id != user_id:
                raise ValueError(f"Username {username} is already in use")

        update_kwargs = {
            k: v for k, v in locals().items() if k != "user_id" and v is not None
        }
        updated = await self._repo.update(user, **update_kwargs)
        logger.info("User %s updated", user_id)

        return UserDTO(
            id=updated.id,
            email=updated.email,
            username=updated.username,
            display_name=updated.display_name,
            phone_number=updated.phone_number,
            avatar_url=updated.avatar_url,
            is_active=updated.is_active,
        )
