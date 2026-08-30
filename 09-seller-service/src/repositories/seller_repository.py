"""Repository: async CRUD operations for the Seller model."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.seller import Seller


async def create_seller(
    session: AsyncSession,
    user_id: uuid.UUID,
    company_name: str,
    inn: str,
    kpp: Optional[str] = None,
    bank_name: Optional[str] = None,
    bank_account: Optional[str] = None,
    bank_bik: Optional[str] = None,
    status: str = "PENDING",
) -> Seller:
    """Insert a new seller record and return it."""
    seller = Seller(
        user_id=user_id,
        company_name=company_name,
        inn=inn,
        kpp=kpp,
        bank_name=bank_name,
        bank_account=bank_account,
        bank_bik=bank_bik,
        status=status,
    )
    session.add(seller)
    await session.flush()
    await session.refresh(seller)
    return seller


async def get_seller_by_id(session: AsyncSession, seller_id: uuid.UUID) -> Optional[Seller]:
    """Fetch a seller by its primary key."""
    result = await session.execute(select(Seller).where(Seller.id == seller_id))
    return result.scalar_one_or_none()


async def get_seller_by_user_id(session: AsyncSession, user_id: uuid.UUID) -> Optional[Seller]:
    """Fetch a seller by the linked user identifier."""
    result = await session.execute(select(Seller).where(Seller.user_id == user_id))
    return result.scalar_one_or_none()


async def get_seller_by_inn(session: AsyncSession, inn: str) -> Optional[Seller]:
    """Fetch a seller by INN (tax identification number)."""
    result = await session.execute(select(Seller).where(Seller.inn == inn))
    return result.scalar_one_or_none()


async def update_seller(
    session: AsyncSession,
    seller: Seller,
    **fields,
) -> Seller:
    """Update mutable fields on *seller* and persist."""
    for key, value in fields.items():
        if hasattr(seller, key) and key not in ("id", "user_id", "created_at"):
            setattr(seller, key, value)
    await session.flush()
    await session.refresh(seller)
    return seller


async def delete_seller(session: AsyncSession, seller: Seller) -> None:
    """Soft-delete: set status to DEACTIVATED."""
    seller.status = "DEACTIVATED"
    await session.flush()


async def list_sellers(
    session: AsyncSession,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Seller]:
    """List sellers with optional status filter."""
    query = select(Seller)
    if status:
        query = query.where(Seller.status == status)
    query = query.order_by(Seller.created_at.desc()).offset(skip).limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())
