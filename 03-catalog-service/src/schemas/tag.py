"""Pydantic schemas for Tag domain."""

from uuid import UUID

from pydantic import BaseModel, Field


class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    metadata: dict | None = None


class TagUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    metadata: dict | None = None
    is_active: bool | None = None


class TagResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    metadata: dict | None = None
    is_active: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class TagListResponse(BaseModel):
    items: list[TagResponse]
    total: int
    skip: int
    limit: int
