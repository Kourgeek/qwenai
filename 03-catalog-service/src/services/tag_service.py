"""Service layer for Tag business logic."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.tag import Tag
from src.repositories.tag_repository import TagRepository


class TagService:
    """Orchestrates tag operations using the repository layer."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = TagRepository(session)

    async def create_tag(self, name: str, slug: str,
                         metadata: dict | None = None) -> Tag:
        if not name or not slug:
            raise ValueError("name and slug are required")
        return await self.repository.create(name=name, slug=slug, metadata=metadata)

    async def get_tag_by_id(self, tag_id: uuid.UUID) -> Tag | None:
        return await self.repository.get_by_id(tag_id)

    async def get_tag_by_slug(self, slug: str) -> Tag | None:
        return await self.repository.get_by_slug(slug)

    async def update_tag(self, tag_id: uuid.UUID,
                         name: str | None = None,
                         metadata: dict | None = None,
                         is_active: bool | None = None) -> Tag | None:
        updates = {}
        if name is not None:
            updates["name"] = name
        if metadata is not None:
            updates["metadata"] = metadata
        if is_active is not None:
            updates["is_active"] = is_active
        return await self.repository.update(tag_id, **updates)

    async def delete_tag(self, tag_id: uuid.UUID) -> bool:
        return await self.repository.delete(tag_id)

    async def list_tags(self, *, skip: int = 0, limit: int = 100,
                        is_active: bool | None = None) -> list[Tag]:
        return await self.repository.list(skip=skip, limit=limit, is_active=is_active)
