"""Repository: async CRUD operations for the SellerProduct model."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.seller import SellerProduct


async def create_seller_product(
    session: AsyncSession,
    seller_id: uuid.UUID,
    product_id: uuid.UUID,
    status: str = "PENDING",
) -> SellerProduct:
    """Create a seller-product mapping."""
    sp = SellerProduct(seller_id=seller_id, product_id=product_id, status=status)
    session.add(sp)
    await session.flush()
    await session.refresh(sp)
    return sp


async def get_seller_product_by_ids(
    session: AsyncSession,
    seller_id: uuid.UUID,
    product_id: uuid.UUID,
) -> Optional[SellerProduct]:
    """Fetch a single seller-product mapping."""
    result = await session.execute(
        select(SellerProduct).where(
            SellerProduct.seller_id == seller_id,
            SellerProduct.product_id == product_id,
        )
    )
    return result.scalar_one_or_none()


async def list_seller_products(
    session: AsyncSession,
    seller_id: uuid.UUID,
    status: Optional[str] = None,
) -> list[SellerProduct]:
    """List all product mappings for a seller."""
    query = select(SellerProduct).where(SellerProduct.seller_id == seller_id)
    if status:
        query = query.where(SellerProduct.status == status)
    result = await session.execute(query.order_by(SellerProduct.created_at.desc()))
    return list(result.scalars().all())


async def update_seller_product_status(
    session: AsyncSession,
    seller_product: SellerProduct,
    status: str,
) -> SellerProduct:
    """Update the status of a seller-product mapping."""
    seller_product.status = status
    await session.flush()
    await session.refresh(seller_product)
    return seller_product


async def delete_seller_product(
    session: AsyncSession,
    seller_product: SellerProduct,
) -> None:
    """Delete a seller-product mapping."""
    await session.delete(seller_product)
