"""Pydantic schemas for Product domain."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    slug: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    category_id: UUID | None = None
    brand_id: UUID | None = None
    seller_id: UUID | None = None
    price: float = Field(..., gt=0)
    compare_at_price: float | None = None
    sku: str | None = None
    stock_quantity: int = Field(default=0, ge=0)
    image_urls: list[str] | None = None
    tag_ids: list[UUID] | None = None
    metadata: dict | None = None


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    price: float | None = Field(None, gt=0)
    category_id: UUID | None = None
    brand_id: UUID | None = None
    seller_id: UUID | None = None
    compare_at_price: float | None = None
    sku: str | None = None
    stock_quantity: int | None = Field(None, ge=0)
    image_urls: list[str] | None = None
    tag_ids: list[UUID] | None = None
    metadata: dict | None = None
    is_active: bool | None = None


class ProductResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None = None
    category_id: UUID | None = None
    brand_id: UUID | None = None
    seller_id: UUID | None = None
    price: float
    compare_at_price: float | None = None
    sku: str | None = None
    stock_quantity: int
    image_urls: list[str] | None = None
    tag_ids: list[UUID] | None = None
    metadata: dict | None = Field(default=None, alias="meta_data")
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}

    @model_validator(mode="before")
    @classmethod
    def convert_datetimes(cls, data):
        if isinstance(data, dict):
            for field in ("created_at", "updated_at"):
                if isinstance(data.get(field), datetime):
                    data[field] = data[field].isoformat()
        return data


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    skip: int
    limit: int
