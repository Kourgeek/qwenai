"""FastAPI router for Brand endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.brand import BrandCreate, BrandListResponse, BrandResponse, BrandUpdate
from src.services.brand_service import BrandService

router = APIRouter(prefix="/brands", tags=["brands"])


@router.post("", response_model=BrandResponse, status_code=201)
async def create_brand(body: BrandCreate, db: AsyncSession = Depends(get_db)):
    service = BrandService(db)
    brand = await service.create_brand(
        name=body.name,
        slug=body.slug,
        description=body.description,
        logo_url=body.logo_url,
        website_url=body.website_url,
        metadata=body.metadata,
    )
    return brand


@router.get("", response_model=BrandListResponse)
async def list_brands(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    is_active: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = BrandService(db)
    brands = await service.list_brands(skip=skip, limit=limit, is_active=is_active)
    return BrandListResponse(
        items=brands,
        total=len(brands),
        skip=skip,
        limit=limit,
    )


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(brand_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = BrandService(db)
    brand = await service.get_brand_by_id(brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail=f"Brand {brand_id} not found")
    return brand


@router.patch("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: uuid.UUID, body: BrandUpdate, db: AsyncSession = Depends(get_db)
):
    service = BrandService(db)
    brand = await service.update_brand(
        brand_id,
        name=body.name,
        description=body.description,
        logo_url=body.logo_url,
        website_url=body.website_url,
        metadata=body.metadata,
        is_active=body.is_active,
    )
    if not brand:
        raise HTTPException(status_code=404, detail=f"Brand {brand_id} not found")
    return brand


@router.delete("/{brand_id}", status_code=204)
async def delete_brand(brand_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = BrandService(db)
    deleted = await service.delete_brand(brand_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Brand {brand_id} not found")


@router.get("/search", response_model=BrandListResponse)
async def search_brands(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = BrandService(db)
    brands = await service.search_brands(q, limit=limit)
    return BrandListResponse(
        items=brands,
        total=len(brands),
        skip=0,
        limit=limit,
    )
