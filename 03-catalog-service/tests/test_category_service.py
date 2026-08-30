"""Tests for CategoryService."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.category import Category
from src.repositories.category_repository import CategoryRepository
from src.services.category_service import CategoryService


class TestCategoryServiceCreate:
    """Tests for CategoryService.create_category."""

    @pytest.mark.asyncio
    async def test_create_category_minimal(self, db_session: AsyncSession):
        service = CategoryService(db_session)
        category = await service.create_category(
            name="Electronics",
            slug="electronics",
        )
        assert category.id is not None
        assert category.name == "Electronics"
        assert category.slug == "electronics"
        assert category.description is None
        assert category.parent_id is None
        assert category.is_active is True
        assert isinstance(category.created_at, datetime)
        assert isinstance(category.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_create_category_full(self, db_session: AsyncSession):
        service = CategoryService(db_session)
        category = await service.create_category(
            name="Laptops",
            slug="laptops",
            description="Portable computers",
            parent_id=None,
            image_urls=["https://example.com/laptop.jpg"],
            metadata={"sort_order": 1},
        )
        assert category.name == "Laptops"
        assert category.slug == "laptops"
        assert category.description == "Portable computers"
        assert category.image_urls == ["https://example.com/laptop.jpg"]
        assert category.metadata == {"sort_order": 1}

    @pytest.mark.asyncio
    async def test_create_category_requires_name_and_slug(self, db_session: AsyncSession):
        service = CategoryService(db_session)
        with pytest.raises(ValueError, match="name and slug are required"):
            await service.create_category(name="", slug="")

    @pytest.mark.asyncio
    async def test_create_category_parent(self, db_session: AsyncSession):
        service = CategoryService(db_session)
        parent = await service.create_category(name="Electronics", slug="electronics")
        child = await service.create_category(
            name="Phones",
            slug="phones",
            parent_id=parent.id,
        )
        assert child.parent_id == parent.id


class TestCategoryServiceGet:
    """Tests for CategoryService get methods."""

    @pytest.mark.asyncio
    async def test_get_category_by_id(self, db_session: AsyncSession):
        service = CategoryService(db_session)
        category = await service.create_category(name="Books", slug="books")
        fetched = await service.get_category_by_id(category.id)
        assert fetched is not None
        assert fetched.id == category.id
        assert fetched.name == "Books"

    @pytest.mark.asyncio
    async def test_get_category_by_id_not_found(self, db_session: AsyncSession):
        service = CategoryService(db_session)
        fake_id = uuid.uuid4()
        fetched = await service.get_category_by_id(fake_id)
        assert fetched is None

    @pytest.mark.asyncio
    async def test_get_category_by_slug(self, db_session: AsyncSession):
        service = CategoryService(db_session)
        category = await service.create_category(name="Toys", slug="toys")
        fetched = await service.get_category_by_slug("toys")
        assert fetched is not None
        assert fetched.name == "Toys"

    @pytest.mark.asyncio
    async def test_get_category_by_slug_not_found(self, db_session: AsyncSession):
        service = CategoryService(db_session)
        fetched = await service.get_category_by_slug("nonexistent")
        assert fetched is None


class TestCategoryServiceUpdate:
    """Tests for CategoryService.update_category."""

    @pytest.mark.asyncio
    async def test_update_category(self, db_session: AsyncSession):
        service = CategoryService(db_session)
        category = await service.create_category(name="Old Name", slug="old-name")
        updated = await service.update_category(
            category.id,
            name="New Name",
            description="Updated description",
        )
        assert updated.name == "New Name"
        assert updated.description == "Updated description"
        assert updated.slug == "old-name"  # slug shouldn't change via update

    @pytest.mark.asyncio
    async def test_update_category_not_found(self, db_session: AsyncSession):
        service = CategoryService(db_session)
        fake_id = uuid.uuid4()
        updated = await service.update_category(fake_id, name="Nope")
        assert updated is None


class TestCategoryServiceDelete:
    """Tests for CategoryService.delete_category."""

    @pytest.mark.asyncio
    async def test_delete_category(self, db_session: AsyncSession):
        service = CategoryService(db_session)
        category = await service.create_category(name="Delete Me", slug="delete-me")
        deleted = await service.delete_category(category.id)
        assert deleted is True
        # Verify it's gone
        fetched = await service.get_category_by_id(category.id)
        assert fetched is None

    @pytest.mark.asyncio
    async def test_delete_category_not_found(self, db_session: AsyncSession):
        service = CategoryService(db_session)
        fake_id = uuid.uuid4()
        deleted = await service.delete_category(fake_id)
        assert deleted is False


class TestCategoryServiceList:
    """Tests for CategoryService.list_categories."""

    @pytest.mark.asyncio
    async def test_list_categories(self, db_session: AsyncSession):
        service = CategoryService(db_session)
        for i in range(5):
            await service.create_category(name=f"Cat {i}", slug=f"cat-{i}")
        categories = await service.list_categories(skip=0, limit=10)
        assert len(categories) == 5

    @pytest.mark.asyncio
    async def test_list_categories_pagination(self, db_session: AsyncSession):
        service = CategoryService(db_session)
        for i in range(5):
            await service.create_category(name=f"Cat {i}", slug=f"cat-{i}")
        page1 = await service.list_categories(skip=0, limit=2)
        page2 = await service.list_categories(skip=2, limit=2)
        assert len(page1) == 2
        assert len(page2) == 2


class TestCategoryServiceTree:
    """Tests for CategoryService tree operations."""

    @pytest.mark.asyncio
    async def test_get_category_tree(self, db_session: AsyncSession):
        service = CategoryService(db_session)
        grandparent = await service.create_category(name="Root", slug="root")
        parent = await service.create_category(name="Child", slug="child", parent_id=grandparent.id)
        tree = await service.get_category_tree(parent.id)
        assert len(tree) == 2
        assert tree[0].name == "Root"
        assert tree[1].name == "Child"

    @pytest.mark.asyncio
    async def test_get_category_children(self, db_session: AsyncSession):
        service = CategoryService(db_session)
        parent = await service.create_category(name="Parent", slug="parent")
        child1 = await service.create_category(name="C1", slug="c1", parent_id=parent.id)
        child2 = await service.create_category(name="C2", slug="c2", parent_id=parent.id)
        children = await service.get_category_children(parent.id)
        assert len(children) == 2
        names = {c.name for c in children}
        assert "C1" in names
        assert "C2" in names
