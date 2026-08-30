"""SQLAlchemy Product model with JSONB fields."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.models.category import Base


class Product(Base):
    """Product with images, tag associations, and arbitrary metadata."""

    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    brand_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    seller_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    compare_at_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True, index=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    image_urls: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    tag_ids: Mapped[list[uuid.UUID] | None] = mapped_column(JSONB, nullable=True)
    meta_data: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
