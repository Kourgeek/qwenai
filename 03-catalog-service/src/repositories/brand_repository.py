"""Repository for Brand CRUD operations (async)."""

import uuid
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.brand import Brand


class BrandRepository:
    """Data access layer for Brand entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, name: str, slug: str, description: str | None = None,
                     logo_url: str | None = None,
                     website_url: str | None = None,
                     metadata: dict | None = None) -> Brand:
        brand = Brand(
            name=name,
            slug=slug,
            description=description,
            logo_url=logo_url,
            website_url=website_url,
            metadata=metadata,
        )
        self.session.add(brand)
        await self.session.flush()
        await self.session.refresh(brand)
        return brand

    async def get_by_id(self, brand_id: uuid.UUID) -> Brand | None:
        return await self.session.get(Brand, brand_id)

    async def get_by_slug(self, slug: str) -> Brand | None:
        result = await self.session.execute(
            select(Brand).where(Brand.slug == slug, Brand.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def update(self, brand_id: uuid.UUID, **kwargs) -> Brand | None:
        result = await self.session.execute(
            select(Brand).where(Brand.id == brand_id)
        )
        brand = result.scalar_one_or_none()
        if brand is None:
            return None
        for key, value in kwargs.items():
            if hasattr(brand, key) and key not in ("updated_at",):
                setattr(brand, key, value)
        await self.session.flush()
        await self.session.refresh(brand)
        return brand

    async def delete(self, brand_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            select(Brand).where(Brand.id == brand_id)
        )
        brand = result.scalar_one_or_none()
        if brand is None:
            return False
        await self.session.delete(brand)
        await self.session.flush()
        return True

    async def list(self, *, skip: int = 0, limit: int = 100,
                   is_active: bool | None = None) -> Sequence[Brand]:
        query = select(Brand).order_by(Brand.created_at.desc()).offset(skip).limit(limit)
        if is_active is not None:
            query = query.where(Brand.is_active == is_active)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def search(self, query_text: str, *, limit: int = 20) -> Sequence[Brand]:
        """Search brands by name (ILIKE)."""
        pattern = f"%{query_text}%"
        result = await self.session.execute(
            select(Brand)
            .where(Brand.name.ilike(pattern), Brand.is_active.is_(True))
            .order_by(Brand.name.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
