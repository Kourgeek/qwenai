"""BFF API routes — FastAPI router."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from src.services.bff_service import BffService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bff", tags=["BFF"])

# Auth sub-router — mounted at /auth by the BFF app
auth_router = APIRouter(prefix="/auth", tags=["Auth"])


def _get_bff_service() -> BffService:
    """Retrieve the BffService instance from FastAPI state."""
    from starlette.requests import Request

    # This is a placeholder; the actual service is injected via lifespan
    # We'll use app.state.bff_service in the router
    return None


# We'll attach the service reference at app startup time
_bff_service: Optional[BffService] = None


def set_bff_service(service: BffService) -> None:
    """Set the BffService instance on the router module."""
    global _bff_service
    _bff_service = service


@router.get("/profile")
async def get_profile(user_id: str = Query(..., description="User ID")) -> dict:
    """Aggregate and return the user profile from user-service."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        return await _bff_service.get_user_profile(user_id)
    except Exception as exc:
        logger.error("Error fetching profile for user_id=%s: %s", user_id, exc)
        raise HTTPException(status_code=502, detail=f"User service unavailable: {exc}")


@router.get("/cart")
async def get_cart(user_id: str = Query(..., description="User ID")) -> dict:
    """Aggregate and return the user shopping cart from cart-service."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        return await _bff_service.get_user_cart(user_id)
    except Exception as exc:
        logger.error("Error fetching cart for user_id=%s: %s", user_id, exc)
        raise HTTPException(status_code=502, detail=f"Cart service unavailable: {exc}")


@router.get("/orders")
async def get_orders(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> dict:
    """Aggregate and return the user orders from order-service."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        return await _bff_service.get_user_orders(user_id, limit=limit, offset=offset)
    except Exception as exc:
        logger.error("Error fetching orders for user_id=%s: %s", user_id, exc)
        raise HTTPException(status_code=502, detail=f"Order service unavailable: {exc}")


@router.get("/search")
async def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    category_id: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    sort_by: str = Query("relevance", regex="^(relevance|price_asc|price_desc|newest)$", description="Sort field"),
) -> dict:
    """Aggregate and return search results from search-service."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        return await _bff_service.search_products(
            query=q,
            limit=limit,
            offset=offset,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
        )
    except Exception as exc:
        logger.error("Error searching products for query='%s': %s", q, exc)
        raise HTTPException(status_code=502, detail=f"Search service unavailable: {exc}")


@router.get("/seller/{seller_id}")
async def get_seller(seller_id: str) -> dict:
    """Fetch seller information from seller-service."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        return await _bff_service.get_seller_info(seller_id)
    except Exception as exc:
        logger.error("Error fetching seller info for seller_id=%s: %s", seller_id, exc)
        raise HTTPException(status_code=502, detail=f"Seller service unavailable: {exc}")


@router.get("/seller/{seller_id}/products")
async def get_seller_products(
    seller_id: str,
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> dict:
    """Fetch products for a seller from catalog-service."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        return await _bff_service.get_seller_products(seller_id, limit=limit, offset=offset)
    except Exception as exc:
        logger.error("Error fetching seller products for seller_id=%s: %s", seller_id, exc)
        raise HTTPException(status_code=502, detail=f"Catalog service unavailable: {exc}")


@router.post("/seller/{seller_id}/products")
async def create_seller_product(seller_id: str, request: Request) -> dict:
    """Create a new product for a seller."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Validate required fields
    if not body.get("name"):
        raise HTTPException(status_code=400, detail="Product name is required")
    if not body.get("price"):
        raise HTTPException(status_code=400, detail="Product price is required")

    try:
        return await _bff_service.create_seller_product(seller_id, body)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error creating product for seller_id=%s: %s", seller_id, exc)
        raise HTTPException(status_code=502, detail=f"Catalog service unavailable: {exc}")


@router.patch("/seller/products/{product_id}")
async def update_seller_product(product_id: str, request: Request) -> dict:
    """Update a product."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    try:
        return await _bff_service.update_seller_product(product_id, body)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error updating product %s: %s", product_id, exc)
        raise HTTPException(status_code=502, detail=f"Catalog service unavailable: {exc}")


@router.delete("/seller/products/{product_id}")
async def delete_seller_product(product_id: str) -> dict:
    """Delete a product."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        deleted = await _bff_service.delete_seller_product(product_id)
        return {"success": deleted, "message": "Product deleted" if deleted else "Product not found"}
    except Exception as exc:
        logger.error("Error deleting product %s: %s", product_id, exc)
        raise HTTPException(status_code=502, detail=f"Catalog service unavailable: {exc}")


@router.get("/seller/{seller_id}/stats")
async def get_seller_stats(seller_id: str) -> dict:
    """Fetch seller statistics."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        return await _bff_service.get_seller_stats(seller_id)
    except Exception as exc:
        logger.error("Error fetching seller stats for seller_id=%s: %s", seller_id, exc)
        raise HTTPException(status_code=502, detail=f"Seller service unavailable: {exc}")


@router.get("/seller/{seller_id}/orders")
async def get_seller_orders(
    seller_id: str,
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> dict:
    """Fetch orders for a seller."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        return await _bff_service.get_seller_orders(seller_id, limit=limit, offset=offset)
    except Exception as exc:
        logger.error("Error fetching seller orders for seller_id=%s: %s", seller_id, exc)
        raise HTTPException(status_code=502, detail=f"Order service unavailable: {exc}")


@router.get("/seller/{seller_id}/categories")
async def get_seller_categories(seller_id: str, is_active: bool = Query(True, description="Filter by active status")) -> dict:
    """Fetch categories for seller product creation."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        return await _bff_service.get_seller_categories(is_active=is_active)
    except Exception as exc:
        logger.error("Error fetching categories: %s", exc)
        raise HTTPException(status_code=502, detail=f"Catalog service unavailable: {exc}")


@router.get("/admin/dashboard")
async def get_dashboard() -> dict:
    """Fetch dashboard statistics from admin-service."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        return await _bff_service.get_dashboard_stats()
    except Exception as exc:
        logger.error("Error fetching dashboard stats: %s", exc)
        raise HTTPException(status_code=502, detail=f"Admin service unavailable: {exc}")


# ------------------------------------------------------------------
# Auth endpoints (proxied to Auth service via gRPC)
# ------------------------------------------------------------------


@auth_router.post("/login")
async def auth_login(request: Request):
    """Authenticate user and return JWT tokens."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    email = body.get("email")
    password = body.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        result = await _bff_service.auth_login(email, password)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Auth login failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Auth service unavailable: {exc}")


@auth_router.post("/register")
async def auth_register(request: Request):
    """Register a new user account."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    email = body.get("email")
    password = body.get("password")
    first_name = body.get("first_name", "")
    last_name = body.get("last_name", "")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        result = await _bff_service.auth_register(email, password, first_name, last_name)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Auth register failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Auth service unavailable: {exc}")


@auth_router.post("/refresh")
async def auth_refresh(request: Request):
    """Refresh access token using refresh token."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    refresh_token = body.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="refresh_token is required")

    try:
        result = await _bff_service.auth_refresh(refresh_token)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Auth refresh failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Auth service unavailable: {exc}")


@auth_router.post("/logout")
async def auth_logout(request: Request):
    """Logout and invalidate refresh token."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        body = await request.json()
    except Exception:
        body = {}

    refresh_token = body.get("refresh_token", "")
    try:
        await _bff_service.auth_logout(refresh_token)
        return {"success": True, "message": "Logged out successfully"}
    except Exception as exc:
        logger.error("Auth logout failed: %s", exc)
        return {"success": True, "message": "Logged out"}


@auth_router.post("/forgot-password")
async def auth_forgot_password(request: Request):
    """Request password reset token."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    email = body.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    try:
        result = await _bff_service.auth_forgot_password(email)
        return result
    except Exception as exc:
        logger.error("Forgot password failed: %s", exc)
        # Return dummy to avoid email enumeration
        return {"email": email, "reset_token": "dummy-reset-token"}


@auth_router.get("/profile")
async def auth_profile(request: Request):
    """Get current user profile."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        user_id = request.state.user.get("user_id") if hasattr(request.state, "user") else None
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        return await _bff_service.get_user_profile(user_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Auth profile failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"User service unavailable: {exc}")


# ------------------------------------------------------------------
# Seller management endpoints
# ------------------------------------------------------------------


@router.post("/seller/register")
async def seller_register(request: Request):
    """Register a new seller account."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    user_id = body.get("user_id")
    business_name = body.get("business_name", "")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        result = await _bff_service.seller_register(user_id, business_name)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Seller register failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Seller service unavailable: {exc}")


@router.get("/seller/{seller_id}/products")
async def get_seller_products(
    seller_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
):
    """Get products for a seller."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        return await _bff_service.get_seller_products(seller_id, limit=limit, offset=offset, status=status)
    except Exception as exc:
        logger.error("Error fetching seller products for seller_id=%s: %s", seller_id, exc)
        raise HTTPException(status_code=502, detail=f"Catalog service unavailable: {exc}")


@router.post("/seller/products")
async def create_seller_product(request: Request):
    """Create a new product for a seller."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    seller_id = body.get("seller_id")
    name = body.get("name")
    price = body.get("price")
    if not seller_id or not name or price is None:
        raise HTTPException(status_code=400, detail="seller_id, name, and price are required")

    try:
        result = await _bff_service.create_seller_product(
            seller_id=seller_id,
            name=name,
            slug=body.get("slug"),
            description=body.get("description"),
            category_id=body.get("category_id"),
            brand_id=body.get("brand_id"),
            price=price,
            compare_at_price=body.get("compare_at_price"),
            sku=body.get("sku"),
            stock_quantity=body.get("stock_quantity", 0),
            image_urls=body.get("image_urls"),
            tag_ids=body.get("tag_ids"),
            metadata=body.get("metadata"),
        )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Create seller product failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Catalog service unavailable: {exc}")


@router.patch("/seller/products/{product_id}")
async def update_seller_product(product_id: str, request: Request):
    """Update a product."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    try:
        result = await _bff_service.update_seller_product(
            product_id=product_id,
            name=body.get("name"),
            description=body.get("description"),
            price=body.get("price"),
            category_id=body.get("category_id"),
            brand_id=body.get("brand_id"),
            compare_at_price=body.get("compare_at_price"),
            sku=body.get("sku"),
            stock_quantity=body.get("stock_quantity"),
            image_urls=body.get("image_urls"),
            tag_ids=body.get("tag_ids"),
            metadata=body.get("metadata"),
            is_active=body.get("is_active"),
        )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Update seller product failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Catalog service unavailable: {exc}")


@router.delete("/seller/products/{product_id}", status_code=204)
async def delete_seller_product(product_id: str):
    """Delete a product."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        await _bff_service.delete_seller_product(product_id)
        return {"success": True}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Delete seller product failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Catalog service unavailable: {exc}")


@router.get("/seller/stats/{seller_id}")
async def get_seller_stats(seller_id: str):
    """Get seller statistics."""
    if _bff_service is None:
        raise HTTPException(status_code=503, detail="BFF service not initialized")
    try:
        return await _bff_service.get_seller_stats(seller_id)
    except Exception as exc:
        logger.error("Error fetching seller stats for seller_id=%s: %s", seller_id, exc)
        raise HTTPException(status_code=502, detail=f"Seller service unavailable: {exc}")
