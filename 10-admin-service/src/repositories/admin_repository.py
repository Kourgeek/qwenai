"""Async CRUD repository for AdminUser."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.admin import AdminUser


class AdminRepository:
    """Data access layer for ``AdminUser`` records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: str) -> AdminUser | None:
        result = await self._session.execute(
            select(AdminUser).where(AdminUser.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, admin_id: uuid.UUID) -> AdminUser | None:
        result = await self._session.execute(
            select(AdminUser).where(AdminUser.id == admin_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str, role: str = "CATALOG_MANAGER") -> AdminUser:
        admin = AdminUser(user_id=user_id, role=role)
        self._session.add(admin)
        await self._session.flush()
        await self._session.refresh(admin)
        return admin

    async def update_role(self, admin_id: uuid.UUID, new_role: str) -> AdminUser | None:
        admin = await self.get_by_id(admin_id)
        if admin is None:
            return None
        admin.role = new_role
        await self._session.flush()
        await self._session.refresh(admin)
        return admin

    async def update_permissions(self, admin_id: uuid.UUID, permissions: dict) -> AdminUser | None:
        admin = await self.get_by_id(admin_id)
        if admin is None:
            return None
        admin.permissions = permissions
        await self._session.flush()
        await self._session.refresh(admin)
        return admin

    async def list_all(self) -> list[AdminUser]:
        result = await self._session.execute(select(AdminUser))
        return list(result.scalars().all())
