"""Repository for Tag CRUD operations (async)."""

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.tag import Tag


class TagRepository:
    """Data access layer for Tag entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, name: str, slug: str,
                     metadata: dict | None = None) -> Tag:
        tag = Tag(
            name=name,
            slug=slug,
            metadata=metadata,
        )
        self.session.add(tag)
        await self.session.flush()
        await self.session.refresh(tag)
        return tag

    async def get_by_id(self, tag_id: uuid.UUID) -> Tag | None:
        return await self.session.get(Tag, tag_id)

    async def get_by_slug(self, slug: str) -> Tag | None:
        result = await self.session.execute(
            select(Tag).where(Tag.slug == slug, Tag.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def update(self, tag_id: uuid.UUID, **kwargs) -> Tag | None:
        result = await self.session.execute(
            select(Tag).where(Tag.id == tag_id)
        )
        tag = result.scalar_one_or_none()
        if tag is None:
            return None
        for key, value in kwargs.items():
            if hasattr(tag, key) and key not in ("updated_at",):
                setattr(tag, key, value)
        await self.session.flush()
        await self.session.refresh(tag)
        return tag

    async def delete(self, tag_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            select(Tag).where(Tag.id == tag_id)
        )
        tag = result.scalar_one_or_none()
        if tag is None:
            return False
        await self.session.delete(tag)
        await self.session.flush()
        return True

    async def list(self, *, skip: int = 0, limit: int = 100,
                   is_active: bool | None = None) -> Sequence[Tag]:
        query = select(Tag).order_by(Tag.created_at.desc()).offset(skip).limit(limit)
        if is_active is not None:
            query = query.where(Tag.is_active == is_active)
        result = await self.session.execute(query)
        return list(result.scalars().all())
