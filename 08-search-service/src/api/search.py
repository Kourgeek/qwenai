"""FastAPI router for the Search Service HTTP API."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Query

from src.services.search_service import SearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


# ✅ type-annotated query params ✅

class SearchQueryParams:
    """Shared query parameters for search endpoints."""

    query: str = ""
    categories: str | None = None
    brands: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    sort_by: str = "_score"
    sort_order: str = "desc"
    page: int = 1
    page_size: int = 20


class SuggestQueryParams:
    """Query parameters for the suggest endpoint."""

    query: str = ""
    limit: int = 10


# ✅ endpoints ✅

@router.get("/products", summary="Search products")
async def search_products(
    query: str = Query(default="", description="Full-text search query"),
    categories: str | None = Query(default=None, description="Comma-separated category filter"),
    brands: str | None = Query(default=None, description="Comma-separated brand filter"),
    min_price: float | None = Query(default=None, ge=0, description="Minimum price"),
    max_price: float | None = Query(default=None, ge=0, description="Maximum price"),
    sort_by: str = Query(default="_score", description="Sort field (price, _score)"),
    sort_order: str = Query(default="desc", description="Sort order (asc, desc)"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Results per page"),
    search_service: Any = None,
) -> dict[str, Any]:
    """Full-text product search with optional filters, sorting, and pagination.

    Query parameters:
        query: Full-text search query
        categories: Comma-separated category filter
        brands: Comma-separated brand filter
        min_price: Minimum price
        max_price: Maximum price
        sort_by: Sort field (price, _score)
        sort_order: Sort order (asc, desc)
        page: Page number
        page_size: Results per page
    """
    # Placeholder implementation
    return {"products": [], "total": 0, "page": page, "page_size": page_size}


@router.get("/suggest", summary="Get product name suggestions")
async def suggest_products(
    query: str = Query(default="", description="Partial product name to suggest"),
    limit: int = Query(default=10, ge=1, le=50, description="Max suggestions to return"),
    search_service: Any = None,
) -> dict[str, Any]:
    """Get product name suggestions based on a partial query.

    Query parameters:
        query: Partial product name to suggest
        limit: Max suggestions to return
    """
    return {"suggestions": []}
