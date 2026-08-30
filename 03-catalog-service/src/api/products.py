"""FastAPI router for Product endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from src.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(body: ProductCreate, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    product = await service.create_product(
        name=body.name,
        slug=body.slug,
        price=body.price,
        description=body.description,
        category_id=body.category_id,
        brand_id=body.brand_id,
        seller_id=body.seller_id,
        compare_at_price=body.compare_at_price,
        sku=body.sku,
        stock_quantity=body.stock_quantity,
        image_urls=body.image_urls,
        tag_ids=body.tag_ids,
        metadata=body.metadata,
    )
    return product


@router.get("", response_model=ProductListResponse)
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    is_active: bool | None = Query(None),
    seller_id: str | None = Query(None, description="Filter by seller ID"),
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    if seller_id:
        import uuid
        try:
            seller_uuid = uuid.UUID(seller_id)
            products = await service.get_products_by_seller(seller_uuid, skip=skip, limit=limit)
        except ValueError:
            products = []
    else:
        products = await service.list_products(skip=skip, limit=limit, is_active=is_active)
    return ProductListResponse(
        items=products,
        total=len(products),
        skip=skip,
        limit=limit,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    product = await service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID, body: ProductUpdate, db: AsyncSession = Depends(get_db)
):
    service = ProductService(db)
    product = await service.update_product(
        product_id,
        name=body.name,
        description=body.description,
        price=body.price,
        category_id=body.category_id,
        brand_id=body.brand_id,
        seller_id=body.seller_id,
        compare_at_price=body.compare_at_price,
        sku=body.sku,
        stock_quantity=body.stock_quantity,
        image_urls=body.image_urls,
        tag_ids=body.tag_ids,
        metadata=body.metadata,
        is_active=body.is_active,
    )
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    deleted = await service.delete_product(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")


@router.get("/search", response_model=ProductListResponse)
async def search_products(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    products = await service.search_products(q, limit=limit)
    return ProductListResponse(
        items=products,
        total=len(products),
        skip=0,
        limit=limit,
    )


@router.get("/by-category/{category_id}", response_model=ProductListResponse)
async def get_products_by_category(
    category_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    products = await service.get_products_by_category(category_id, skip=skip, limit=limit)
    return ProductListResponse(
        items=products,
        total=len(products),
        skip=skip,
        limit=limit,
    )


@router.get("/by-tag/{tag_id}", response_model=ProductListResponse)
async def get_products_by_tag(
    tag_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    products = await service.get_products_by_tag(tag_id, skip=skip, limit=limit)
    return ProductListResponse(
        items=products,
        total=len(products),
        skip=skip,
        limit=limit,
    )
