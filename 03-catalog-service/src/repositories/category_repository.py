"""Repository for Category CRUD operations (async)."""

import uuid
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.category import Category


class CategoryRepository:
    """Data access layer for Category entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, name: str, slug: str, description: str | None = None,
                     parent_id: uuid.UUID | None = None,
                     image_urls: list[str] | None = None,
                     metadata: dict | None = None) -> Category:
        category = Category(
            name=name,
            slug=slug,
            description=description,
            parent_id=parent_id,
            image_urls=image_urls,
            metadata=metadata,
        )
        self.session.add(category)
        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        return await self.session.get(Category, category_id)

    async def get_by_slug(self, slug: str) -> Category | None:
        result = await self.session.execute(
            select(Category).where(Category.slug == slug, Category.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def update(self, category_id: uuid.UUID, **kwargs) -> Category | None:
        result = await self.session.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()
        if category is None:
            return None
        for key, value in kwargs.items():
            if hasattr(category, key) and key not in ("updated_at",):
                setattr(category, key, value)
        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def delete(self, category_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()
        if category is None:
            return False
        await self.session.delete(category)
        await self.session.flush()
        return True

    async def list(self, *, skip: int = 0, limit: int = 100,
                   is_active: bool | None = None,
                   parent_id: uuid.UUID | None = None) -> Sequence[Category]:
        query = select(Category).order_by(Category.created_at.desc()).offset(skip).limit(limit)
        if is_active is not None:
            query = query.where(Category.is_active == is_active)
        if parent_id is not None:
            query = query.where(Category.parent_id == parent_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.session.execute(select(Category).where(Category.is_active.is_(True)))
        return len(list(result.scalars().all()))
