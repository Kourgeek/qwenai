"""FastAPI router for Tag endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.tag import TagCreate, TagListResponse, TagResponse, TagUpdate
from src.services.tag_service import TagService

router = APIRouter(prefix="/tags", tags=["tags"])


@router.post("", response_model=TagResponse, status_code=201)
async def create_tag(body: TagCreate, db: AsyncSession = Depends(get_db)):
    service = TagService(db)
    tag = await service.create_tag(
        name=body.name,
        slug=body.slug,
        metadata=body.metadata,
    )
    return tag


@router.get("", response_model=TagListResponse)
async def list_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    is_active: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = TagService(db)
    tags = await service.list_tags(skip=skip, limit=limit, is_active=is_active)
    return TagListResponse(
        items=tags,
        total=len(tags),
        skip=skip,
        limit=limit,
    )


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(tag_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = TagService(db)
    tag = await service.get_tag_by_id(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")
    return tag


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: uuid.UUID, body: TagUpdate, db: AsyncSession = Depends(get_db)
):
    service = TagService(db)
    tag = await service.update_tag(
        tag_id,
        name=body.name,
        metadata=body.metadata,
        is_active=body.is_active,
    )
    if not tag:
        raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")
    return tag


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(tag_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = TagService(db)
    deleted = await service.delete_tag(tag_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")
