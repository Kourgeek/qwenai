"""Service layer for Category business logic."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.category import Category
from src.repositories.category_repository import CategoryRepository


class CategoryService:
    """Orchestrates category operations using the repository layer."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = CategoryRepository(session)

    async def create_category(self, name: str, slug: str,
                              description: str | None = None,
                              parent_id: uuid.UUID | None = None,
                              image_urls: list[str] | None = None,
                              metadata: dict | None = None) -> Category:
        if not name or not slug:
            raise ValueError("name and slug are required")
        return await self.repository.create(
            name=name, slug=slug,
            description=description,
            parent_id=parent_id,
            image_urls=image_urls,
            metadata=metadata,
        )

    async def get_category_by_id(self, category_id: uuid.UUID) -> Category | None:
        return await self.repository.get_by_id(category_id)

    async def get_category_by_slug(self, slug: str) -> Category | None:
        return await self.repository.get_by_slug(slug)

    async def update_category(self, category_id: uuid.UUID,
                              name: str | None = None,
                              description: str | None = None,
                              parent_id: uuid.UUID | None = None,
                              image_urls: list[str] | None = None,
                              metadata: dict | None = None,
                              is_active: bool | None = None) -> Category | None:
        updates = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if parent_id is not None:
            updates["parent_id"] = parent_id
        if image_urls is not None:
            updates["image_urls"] = image_urls
        if metadata is not None:
            updates["metadata"] = metadata
        if is_active is not None:
            updates["is_active"] = is_active
        return await self.repository.update(category_id, **updates)

    async def delete_category(self, category_id: uuid.UUID) -> bool:
        return await self.repository.delete(category_id)

    async def list_categories(self, *, skip: int = 0, limit: int = 100,
                              is_active: bool | None = None,
                              parent_id: uuid.UUID | None = None) -> list[Category]:
        return await self.repository.list(
            skip=skip, limit=limit,
            is_active=is_active,
            parent_id=parent_id,
        )

    async def get_category_tree(self, category_id: uuid.UUID) -> list[Category]:
        """Build the full ancestry path for a category."""
        category = await self.get_category_by_id(category_id)
        if category is None:
            return []
        path: list[Category] = [category]
        current = category
        while current.parent_id is not None:
            parent = await self.get_category_by_id(current.parent_id)
            if parent is None:
                break
            path.insert(0, parent)
            current = parent
        return path

    async def get_category_children(self, category_id: uuid.UUID) -> list[Category]:
        """Get direct children of a category."""
        return await self.repository.list(parent_id=category_id)
