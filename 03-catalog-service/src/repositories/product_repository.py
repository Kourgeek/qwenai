"""Repository for Product CRUD operations (async)."""

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.product import Product


class ProductRepository:
    """Data access layer for Product entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, name: str, slug: str, price: float,
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
        product = Product(
            name=name,
            slug=slug,
            description=description,
            category_id=category_id,
            brand_id=brand_id,
            seller_id=seller_id,
            price=price,
            compare_at_price=compare_at_price,
            sku=sku,
            stock_quantity=stock_quantity,
            image_urls=image_urls,
            tag_ids=tag_ids,
            metadata=metadata,
        )
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        return await self.session.get(Product, product_id)

    async def get_by_slug(self, slug: str) -> Product | None:
        result = await self.session.execute(
            select(Product).where(Product.slug == slug, Product.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def update(self, product_id: uuid.UUID, **kwargs) -> Product | None:
        result = await self.session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        if product is None:
            return None
        for key, value in kwargs.items():
            if hasattr(product, key) and key not in ("updated_at",):
                setattr(product, key, value)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def delete(self, product_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        if product is None:
            return False
        await self.session.delete(product)
        await self.session.flush()
        return True

    async def list(self, *, skip: int = 0, limit: int = 100,
                   is_active: bool | None = None) -> Sequence[Product]:
        query = select(Product).order_by(Product.created_at.desc()).offset(skip).limit(limit)
        if is_active is not None:
            query = query.where(Product.is_active == is_active)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def search(self, query_text: str, *, limit: int = 20) -> Sequence[Product]:
        """Search products by name (ILIKE)."""
        pattern = f"%{query_text}%"
        result = await self.session.execute(
            select(Product)
            .where(Product.name.ilike(pattern), Product.is_active.is_(True))
            .order_by(Product.name.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_category(self, category_id: uuid.UUID, *, skip: int = 0,
                              limit: int = 100) -> Sequence[Product]:
        """Get products belonging to a category."""
        result = await self.session.execute(
            select(Product)
            .where(Product.category_id == category_id, Product.is_active.is_(True))
            .order_by(Product.name.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_tag(self, tag_id: uuid.UUID, *, skip: int = 0,
                         limit: int = 100) -> Sequence[Product]:
        """Get products that have a given tag in their tag_ids JSONB array."""
        result = await self.session.execute(
            select(Product)
            .where(Product.tag_ids.contains([str(tag_id)]),
                   Product.is_active.is_(True))
            .order_by(Product.name.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_seller(self, seller_id: uuid.UUID, *, skip: int = 0,
                            limit: int = 100) -> Sequence[Product]:
        """Get products belonging to a seller."""
        result = await self.session.execute(
            select(Product)
            .where(Product.seller_id == seller_id)
            .order_by(Product.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
