"""FastAPI router for Category endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.category import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdate,
)
from src.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(body: CategoryCreate, db: AsyncSession = Depends(get_db)):
    service = CategoryService(db)
    category = await service.create_category(
        name=body.name,
        slug=body.slug,
        description=body.description,
        parent_id=body.parent_id,
        image_urls=body.image_urls,
        metadata=body.metadata,
    )
    return category


@router.get("", response_model=CategoryListResponse)
async def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    is_active: bool | None = Query(None),
    parent_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = CategoryService(db)
    cat_parent_id = uuid.UUID(parent_id) if parent_id else None
    categories = await service.list_categories(
        skip=skip, limit=limit, is_active=is_active, parent_id=cat_parent_id
    )
    return CategoryListResponse(
        items=categories,
        total=len(categories),
        skip=skip,
        limit=limit,
    )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = CategoryService(db)
    category = await service.get_category_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail=f"Category {category_id} not found")
    return category


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: uuid.UUID, body: CategoryUpdate, db: AsyncSession = Depends(get_db)
):
    service = CategoryService(db)
    category = await service.update_category(
        category_id,
        name=body.name,
        description=body.description,
        parent_id=body.parent_id,
        image_urls=body.image_urls,
        metadata=body.metadata,
        is_active=body.is_active,
    )
    if not category:
        raise HTTPException(status_code=404, detail=f"Category {category_id} not found")
    return category


@router.delete("/{category_id}", status_code=204)
async def delete_category(category_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = CategoryService(db)
    deleted = await service.delete_category(category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Category {category_id} not found")
