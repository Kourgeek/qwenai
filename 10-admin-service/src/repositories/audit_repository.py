"""Async CRUD repository for AuditLog."""

import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.admin import AuditLog


class AuditRepository:
    """Data access layer for ``AuditLog`` records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        admin_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        old_values: dict | None = None,
        new_values: dict | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        log = AuditLog(
            admin_id=admin_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
        )
        self._session.add(log)
        await self._session.flush()
        await self._session.refresh(log)
        return log

    async def get_by_admin(
        self,
        admin_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        result = await self._session.execute(
            select(AuditLog)
            .where(AuditLog.admin_id == admin_id)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        result = await self._session.execute(
            select(AuditLog)
            .where(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_all(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        result = await self._session.execute(
            select(AuditLog)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
