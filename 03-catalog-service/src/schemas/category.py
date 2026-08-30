"""Pydantic schemas for Category domain."""

from uuid import UUID

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    parent_id: UUID | None = None
    image_urls: list[str] | None = None
    metadata: dict | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    parent_id: UUID | None = None
    image_urls: list[str] | None = None
    metadata: dict | None = None
    is_active: bool | None = None


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None = None
    parent_id: UUID | None = None
    image_urls: list[str] | None = None
    metadata: dict | None = None
    is_active: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class CategoryListResponse(BaseModel):
    items: list[CategoryResponse]
    total: int
    skip: int
    limit: int
