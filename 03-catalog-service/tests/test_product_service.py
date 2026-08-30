"""Tests for ProductService."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.product_repository import ProductRepository
from src.services.product_service import ProductService


class TestProductServiceCreate:
    """Tests for ProductService.create_product."""

    @pytest.mark.asyncio
    async def test_create_product_minimal(self, db_session: AsyncSession):
        service = ProductService(db_session)
        product = await service.create_product(
            name="Widget",
            slug="widget",
            price=9.99,
        )
        assert product.id is not None
        assert product.name == "Widget"
        assert product.price == 9.99
        assert product.stock_quantity == 0
        assert product.is_active is True

    @pytest.mark.asyncio
    async def test_create_product_full(self, db_session: AsyncSession):
        service = ProductService(db_session)
        category = await __import__("src.services.category_service", fromlist=["CategoryService"]).CategoryService(db_session).create_category(
            name="Electronics", slug="electronics"
        )
        brand = await __import__("src.services.brand_service", fromlist=["BrandService"]).BrandService(db_session).create_brand(
            name="Acme", slug="acme"
        )
        tag = await __import__("src.services.tag_service", fromlist=["TagService"]).TagService(db_session).create_tag(
            name="New", slug="new"
        )

        product = await service.create_product(
            name="Super Widget",
            slug="super-widget",
            price=29.99,
            description="A super widget",
            category_id=category.id,
            brand_id=brand.id,
            compare_at_price=39.99,
            sku="SW-001",
            stock_quantity=100,
            image_urls=["https://example.com/widget.jpg"],
            tag_ids=[tag.id],
            metadata={"weight_kg": 0.5},
        )
        assert product.name == "Super Widget"
        assert product.price == 29.99
        assert product.compare_at_price == 39.99
        assert product.sku == "SW-001"
        assert product.stock_quantity == 100
        assert product.category_id == category.id
        assert product.brand_id == brand.id
        assert product.image_urls == ["https://example.com/widget.jpg"]
        assert product.tag_ids == [tag.id]
        assert product.metadata == {"weight_kg": 0.5}

    @pytest.mark.asyncio
    async def test_create_product_requires_fields(self, db_session: AsyncSession):
        service = ProductService(db_session)
        with pytest.raises(ValueError, match="name and slug are required"):
            await service.create_product(name="", slug="", price=1.0)

    @pytest.mark.asyncio
    async def test_create_product_requires_price(self, db_session: AsyncSession):
        service = ProductService(db_session)
        with pytest.raises(ValueError, match="price is required"):
            await service.create_product(name="X", slug="x", price=None)


class TestProductServiceGet:
    """Tests for ProductService get methods."""

    @pytest.mark.asyncio
    async def test_get_product_by_id(self, db_session: AsyncSession):
        service = ProductService(db_session)
        product = await service.create_product(name="Gadget", slug="gadget", price=15.0)
        fetched = await service.get_product_by_id(product.id)
        assert fetched is not None
        assert fetched.id == product.id
        assert fetched.name == "Gadget"

    @pytest.mark.asyncio
    async def test_get_product_by_id_not_found(self, db_session: AsyncSession):
        service = ProductService(db_session)
        fetched = await service.get_product_by_id(uuid.uuid4())
        assert fetched is None

    @pytest.mark.asyncio
    async def test_get_product_by_slug(self, db_session: AsyncSession):
        service = ProductService(db_session)
        product = await service.create_product(name="Gizmo", slug="gizmo", price=5.0)
        fetched = await service.get_product_by_slug("gizmo")
        assert fetched is not None
        assert fetched.name == "Gizmo"


class TestProductServiceUpdate:
    """Tests for ProductService.update_product."""

    @pytest.mark.asyncio
    async def test_update_product(self, db_session: AsyncSession):
        service = ProductService(db_session)
        product = await service.create_product(name="Old", slug="old", price=10.0)
        updated = await service.update_product(product.id, name="New", price=20.0)
        assert updated.name == "New"
        assert updated.price == 20.0
        assert updated.slug == "old"

    @pytest.mark.asyncio
    async def test_update_product_not_found(self, db_session: AsyncSession):
        service = ProductService(db_session)
        updated = await service.update_product(uuid.uuid4(), name="Nope")
        assert updated is None


class TestProductServiceDelete:
    """Tests for ProductService.delete_product."""

    @pytest.mark.asyncio
    async def test_delete_product(self, db_session: AsyncSession):
        service = ProductService(db_session)
        product = await service.create_product(name="Delete Me", slug="delete-me", price=1.0)
        deleted = await service.delete_product(product.id)
        assert deleted is True
        fetched = await service.get_product_by_id(product.id)
        assert fetched is None

    @pytest.mark.asyncio
    async def test_delete_product_not_found(self, db_session: AsyncSession):
        service = ProductService(db_session)
        deleted = await service.delete_product(uuid.uuid4())
        assert deleted is False


class TestProductServiceList:
    """Tests for ProductService.list_products."""

    @pytest.mark.asyncio
    async def test_list_products(self, db_session: AsyncSession):
        service = ProductService(db_session)
        for i in range(3):
            await service.create_product(name=f"Item {i}", slug=f"item-{i}", price=float(i))
        products = await service.list_products(skip=0, limit=10)
        assert len(products) == 3

    @pytest.mark.asyncio
    async def test_list_products_pagination(self, db_session: AsyncSession):
        service = ProductService(db_session)
        for i in range(5):
            await service.create_product(name=f"P {i}", slug=f"p-{i}", price=float(i))
        page1 = await service.list_products(skip=0, limit=2)
        page2 = await service.list_products(skip=2, limit=2)
        assert len(page1) == 2
        assert len(page2) == 2


class TestProductServiceSearch:
    """Tests for ProductService.search_products."""

    @pytest.mark.asyncio
    async def test_search_products(self, db_session: AsyncSession):
        service = ProductService(db_session)
        await service.create_product(name="Wireless Mouse", slug="wireless-mouse", price=25.0)
        await service.create_product(name="Wired Keyboard", slug="wired-keyboard", price=45.0)
        results = await service.search_products("wire", limit=10)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_products_no_match(self, db_session: AsyncSession):
        service = ProductService(db_session)
        await service.create_product(name="Widget", slug="widget", price=1.0)
        results = await service.search_products("nonexistent", limit=10)
        assert len(results) == 0


class TestProductServiceByCategory:
    """Tests for ProductService.get_products_by_category."""

    @pytest.mark.asyncio
    async def test_get_products_by_category(self, db_session: AsyncSession):
        service = ProductService(db_session)
        cat = await __import__("src.services.category_service", fromlist=["CategoryService"]).CategoryService(db_session).create_category(
            name="TestCat", slug="testcat"
        )
        p1 = await service.create_product(name="P1", slug="p1", price=1.0, category_id=cat.id)
        p2 = await service.create_product(name="P2", slug="p2", price=2.0, category_id=cat.id)
        products = await service.get_products_by_category(cat.id)
        assert len(products) == 2
        ids = {p.id for p in products}
        assert p1.id in ids
        assert p2.id in ids
