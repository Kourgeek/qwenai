"""SQLAlchemy ORM models for the Seller domain."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

import uuid


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class Seller(Base):
    """Seller entity representing a registered business seller."""

    __tablename__ = "sellers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, index=True
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    inn: Mapped[str] = mapped_column(String(12), unique=True, nullable=False, index=True)
    kpp: Mapped[str] = mapped_column(String(9), nullable=True)
    bank_name: Mapped[str] = mapped_column(String(255), nullable=True)
    bank_account: Mapped[str] = mapped_column(String(20), nullable=True)
    bank_bik: Mapped[str] = mapped_column(String(9), nullable=True)

    # PENDING, APPROVED, REJECTED, DEACTIVATED
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    seller_products: Mapped[list["SellerProduct"]] = relationship(
        "SellerProduct", back_populates="seller", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Seller(id={self.id}, company_name={self.company_name}, status={self.status})>"


class SellerProduct(Base):
    """Mapping between sellers and their products."""

    __tablename__ = "seller_products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    # PENDING, APPROVED, REJECTED
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    seller: Mapped["Seller"] = relationship("Seller", back_populates="seller_products")

    def __repr__(self) -> str:
        return f"<SellerProduct(seller_id={self.seller_id}, product_id={self.product_id}, status={self.status})>"
