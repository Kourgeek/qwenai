"""Service layer for Brand business logic."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.brand import Brand
from src.repositories.brand_repository import BrandRepository


class BrandService:
    """Orchestrates brand operations using the repository layer."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = BrandRepository(session)

    async def create_brand(self, name: str, slug: str,
                           description: str | None = None,
                           logo_url: str | None = None,
                           website_url: str | None = None,
                           metadata: dict | None = None) -> Brand:
        if not name or not slug:
            raise ValueError("name and slug are required")
        return await self.repository.create(
            name=name, slug=slug,
            description=description,
            logo_url=logo_url,
            website_url=website_url,
            metadata=metadata,
        )

    async def get_brand_by_id(self, brand_id: uuid.UUID) -> Brand | None:
        return await self.repository.get_by_id(brand_id)

    async def get_brand_by_slug(self, slug: str) -> Brand | None:
        return await self.repository.get_by_slug(slug)

    async def update_brand(self, brand_id: uuid.UUID,
                           name: str | None = None,
                           description: str | None = None,
                           logo_url: str | None = None,
                           website_url: str | None = None,
                           metadata: dict | None = None,
                           is_active: bool | None = None) -> Brand | None:
        updates = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if logo_url is not None:
            updates["logo_url"] = logo_url
        if website_url is not None:
            updates["website_url"] = website_url
        if metadata is not None:
            updates["metadata"] = metadata
        if is_active is not None:
            updates["is_active"] = is_active
        return await self.repository.update(brand_id, **updates)

    async def delete_brand(self, brand_id: uuid.UUID) -> bool:
        return await self.repository.delete(brand_id)

    async def list_brands(self, *, skip: int = 0, limit: int = 100,
                          is_active: bool | None = None) -> list[Brand]:
        return await self.repository.list(skip=skip, limit=limit, is_active=is_active)

    async def search_brands(self, query: str, *, limit: int = 20) -> list[Brand]:
        return await self.repository.search(query, limit=limit)
