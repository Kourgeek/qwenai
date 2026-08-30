"""Pydantic schemas for Brand domain."""

from uuid import UUID

from pydantic import BaseModel, Field


class BrandCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    logo_url: str | None = None
    website_url: str | None = None
    metadata: dict | None = None


class BrandUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    logo_url: str | None = None
    website_url: str | None = None
    metadata: dict | None = None
    is_active: bool | None = None


class BrandResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None = None
    logo_url: str | None = None
    website_url: str | None = None
    metadata: dict | None = None
    is_active: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class BrandListResponse(BaseModel):
    items: list[BrandResponse]
    total: int
    skip: int
    limit: int
