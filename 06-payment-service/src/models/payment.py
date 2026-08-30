"""
SQLAlchemy ORM models for the Payment domain.
"""

import enum
from datetime import datetime, timezone

from decimal import Decimal

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, relationship


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentProvider(str, enum.Enum):
    STRIPE = "STRIPE"
    YOOMONEY = "YOOMONEY"


class RefundStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class Payment(Base):
    """Represents a single payment attempt."""

    __tablename__ = "payments"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    order_id = Column(String(100), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="RUB")
    status = Column(Enum(PaymentStatus, name="payment_status"), nullable=False, default=PaymentStatus.PENDING)
    provider = Column(Enum(PaymentProvider, name="payment_provider"), nullable=False)
    provider_payment_id = Column(String(255), nullable=True, index=True)
    provider_error = Column(Text, nullable=True)
    payment_method_id = Column(PG_UUID(as_uuid=True), ForeignKey("payment_methods.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    paid_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    payment_method = relationship("PaymentMethod", back_populates="payments", foreign_keys=[payment_method_id])
    refunds = relationship("Refund", back_populates="payment", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Payment id={self.id} order_id={self.order_id} status={self.status.value}>"


class PaymentMethod(Base):
    """Stored payment method for a user (card, bank account, etc.)."""

    __tablename__ = "payment_methods"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # 'card', 'bank_account', etc.
    last_four = Column(String(4), nullable=True)
    expiry = Column(String(7), nullable=True)  # MM/YY
    is_default = Column(Integer, nullable=False, default=0)  # 0 or 1
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    payments = relationship("Payment", back_populates="payment_method", foreign_keys="Payment.payment_method_id")

    def __repr__(self) -> str:
        return f"<PaymentMethod id={self.id} type={self.type} last_four={self.last_four}>"


class Refund(Base):
    """Represents a refund against a payment."""

    __tablename__ = "refunds"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    payment_id = Column(PG_UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="RUB")
    status = Column(Enum(RefundStatus, name="refund_status"), nullable=False, default=RefundStatus.PENDING)
    provider_refund_id = Column(String(255), nullable=True, index=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    refunded_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    payment = relationship("Payment", back_populates="refunds")

    def __repr__(self) -> str:
        return f"<Refund id={self.id} payment_id={self.payment_id} status={self.status.value}>"
