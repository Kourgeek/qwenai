"""Async CRUD repository for User and RefreshToken models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import RefreshToken, User


class AuthRepository:
    """Data-access layer backed by SQLAlchemy async."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── User ──────────────────────────────────────────────────────────

    async def create_user(
        self,
        email: str,
        hashed_password: str,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    # ── RefreshToken ──────────────────────────────────────────────────

    async def create_refresh_token(
        self,
        user_id: uuid.UUID,
        token: str,
        expires_at: datetime,
    ) -> RefreshToken:
        rt = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )
        self.db.add(rt)
        await self.db.flush()
        await self.db.refresh(rt)
        return rt

    async def get_valid_refresh_token(self, token: str) -> RefreshToken | None:
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token == token,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    async def revoke_token(self, token: str) -> None:
        await self.db.execute(
            RefreshToken.__table__.update()
            .where(RefreshToken.token == token)
            .values(is_revoked=True, updated_at=datetime.now(timezone.utc))
        )

    async def revoke_all_user_tokens(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            RefreshToken.__table__.update()
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,
            )
            .values(is_revoked=True, updated_at=datetime.now(timezone.utc))
        )
