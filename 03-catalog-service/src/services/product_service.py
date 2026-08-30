"""Service layer for Product business logic."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.product import Product
from src.repositories.product_repository import ProductRepository


class ProductService:
    """Orchestrates product operations using the repository layer."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ProductRepository(session)

    async def create_product(self, name: str, slug: str, price: float,
                             description: str | None = None,
                             category_id: uuid.UUID | None = None,
                             brand_id: uuid.UUID | None = None,
                             seller_id: uuid.UUID | None = None,
                             compare_at_price: float | None = None,
                             sku: str | None = None,
                             stock_quantity: int = 0,
                             image_urls: list[str] | None = None,
                             tag_ids: list[uuid.UUID] | None = None,
                             metadata: dict | None = None) -> Product:
        if not name or not slug:
            raise ValueError("name and slug are required")
        if price is None:
            raise ValueError("price is required")
        return await self.repository.create(
            name=name, slug=slug, price=price,
            description=description,
            category_id=category_id,
            brand_id=brand_id,
            seller_id=seller_id,
            compare_at_price=compare_at_price,
            sku=sku,
            stock_quantity=stock_quantity,
            image_urls=image_urls,
            tag_ids=tag_ids,
            metadata=metadata,
        )

    async def get_product_by_id(self, product_id: uuid.UUID) -> Product | None:
        return await self.repository.get_by_id(product_id)

    async def get_product_by_slug(self, slug: str) -> Product | None:
        return await self.repository.get_by_slug(slug)

    async def update_product(self, product_id: uuid.UUID,
                             name: str | None = None,
                             description: str | None = None,
                             price: float | None = None,
                             category_id: uuid.UUID | None = None,
                             brand_id: uuid.UUID | None = None,
                             seller_id: uuid.UUID | None = None,
                             compare_at_price: float | None = None,
                             sku: str | None = None,
                             stock_quantity: int | None = None,
                             image_urls: list[str] | None = None,
                             tag_ids: list[uuid.UUID] | None = None,
                             metadata: dict | None = None,
                             is_active: bool | None = None) -> Product | None:
        updates = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if price is not None:
            updates["price"] = price
        if category_id is not None:
            updates["category_id"] = category_id
        if brand_id is not None:
            updates["brand_id"] = brand_id
        if seller_id is not None:
            updates["seller_id"] = seller_id
        if compare_at_price is not None:
            updates["compare_at_price"] = compare_at_price
        if sku is not None:
            updates["sku"] = sku
        if stock_quantity is not None:
            updates["stock_quantity"] = stock_quantity
        if image_urls is not None:
            updates["image_urls"] = image_urls
        if tag_ids is not None:
            updates["tag_ids"] = tag_ids
        if metadata is not None:
            updates["metadata"] = metadata
        if is_active is not None:
            updates["is_active"] = is_active
        return await self.repository.update(product_id, **updates)

    async def delete_product(self, product_id: uuid.UUID) -> bool:
        return await self.repository.delete(product_id)

    async def list_products(self, *, skip: int = 0, limit: int = 100,
                            is_active: bool | None = None) -> list[Product]:
        return await self.repository.list(skip=skip, limit=limit, is_active=is_active)

    async def search_products(self, query: str, *, limit: int = 20) -> list[Product]:
        return await self.repository.search(query, limit=limit)

    async def get_products_by_category(self, category_id: uuid.UUID,
                                        *, skip: int = 0, limit: int = 100) -> list[Product]:
        return await self.repository.get_by_category(category_id, skip=skip, limit=limit)

    async def get_products_by_tag(self, tag_id: uuid.UUID,
                                   *, skip: int = 0, limit: int = 100) -> list[Product]:
        return await self.repository.get_by_tag(tag_id, skip=skip, limit=limit)

    async def get_products_by_seller(self, seller_id: uuid.UUID,
                                     *, skip: int = 0, limit: int = 100) -> list[Product]:
        return await self.repository.get_by_seller(seller_id, skip=skip, limit=limit)
