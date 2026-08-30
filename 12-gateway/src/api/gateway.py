"""Gateway API routes — FastAPI router.

Handles public endpoints (health, auth, product browsing) and
proxies authenticated requests to the BFF service.
"""

import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from src.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Gateway"])


# ------------------------------------------------------------------
# Health
# ------------------------------------------------------------------


@router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "gateway",
        "version": "1.0.0",
        "bff_service": f"http://{settings.bff_service_host}:{settings.bff_service_port}",
    }


# ------------------------------------------------------------------
# Auth endpoints (proxied to BFF / Auth service)
# ------------------------------------------------------------------


@router.post("/auth/login")
async def auth_login(request: Request):
    """Authenticate user — proxy to auth-service HTTP."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                f"http://auth-service:8080/auth/login",
                json={"email": email, "password": password},
            )
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            else:
                logger.error("Auth login proxy failed: %d %s", resp.status_code, resp.text)
                raise HTTPException(status_code=502, detail="Auth service unavailable")
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Auth service unavailable")


@router.post("/auth/register")
async def auth_register(request: Request):
    """Register a new user — proxy to auth-service HTTP."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    email = body.get("email")
    password = body.get("password")
    first_name = body.get("first_name")
    last_name = body.get("last_name")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                f"http://auth-service:8080/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
            if resp.status_code in (200, 201):
                return resp.json()
            elif resp.status_code == 409:
                raise HTTPException(status_code=409, detail="Email already registered")
            else:
                logger.error("Auth register proxy failed: %d %s", resp.status_code, resp.text)
                raise HTTPException(status_code=502, detail="Auth service unavailable")
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Auth service unavailable")


@router.post("/auth/refresh")
async def auth_refresh(request: Request):
    """Refresh access token using refresh token."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    refresh_token = body.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="refresh_token is required")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                f"{settings.bff_service_url}/auth/refresh",
                json={"refresh_token": refresh_token},
            )
            if resp.status_code in (200, 201):
                return resp.json()
            else:
                raise HTTPException(status_code=401, detail="Invalid refresh token")
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="BFF service unavailable")


@router.post("/auth/logout")
async def auth_logout(request: Request):
    """Logout and invalidate refresh token."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    refresh_token = body.get("refresh_token", "")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                f"{settings.bff_service_url}/auth/logout",
                json={"refresh_token": refresh_token},
            )
            return {"success": True, "message": "Logged out"}
        except httpx.ConnectError:
            return {"success": True, "message": "Logged out"}


@router.post("/auth/forgot-password")
async def auth_forgot_password(request: Request):
    """Request password reset token."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    email = body.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                f"{settings.bff_service_url}/auth/forgot-password",
                json={"email": email},
            )
            return resp.json()
        except httpx.ConnectError:
            return {"email": email, "reset_token": "dummy-reset-token"}


@router.get("/auth/profile")
async def auth_profile(request: Request):
    """Get current user profile from user-service via BFF."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                f"{settings.bff_service_url}/bff/profile",
                params={"user_id": user_id},
            )
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=502, detail="User service unavailable")
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="BFF service unavailable")


# ------------------------------------------------------------------
# Product endpoints (public — no auth required)
# ------------------------------------------------------------------


@router.get("/products")
async def get_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category_id: Optional[str] = Query(None, description="Filter by category"),
):
    """Get product listing — proxied to BFF service."""
    offset = (page - 1) * page_size
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                f"{settings.bff_service_url}/bff/search",
                params={"q": "", "limit": page_size, "offset": offset, "category_id": category_id},
            )
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=502, detail="BFF service unavailable")
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="BFF service unavailable")


@router.get("/products/search")
async def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    category_id: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    sort_by: str = Query("relevance", description="Sort field"),
):
    """Search products — proxied to BFF service."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                f"{settings.bff_service_url}/bff/search",
                params={
                    "q": q,
                    "limit": limit,
                    "offset": offset,
                    "category_id": category_id,
                    "min_price": min_price,
                    "max_price": max_price,
                    "sort_by": sort_by,
                },
            )
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=502, detail="BFF service unavailable")
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="BFF service unavailable")


# ------------------------------------------------------------------
# Cart endpoint (authenticated)
# ------------------------------------------------------------------


@router.post("/cart")
async def add_to_cart(request: Request):
    """Add item to shopping cart — proxied to BFF service.

    Requires authentication via Bearer token.
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    product_id = body.get("product_id")
    quantity = body.get("quantity", 1)

    if not product_id:
        raise HTTPException(status_code=400, detail="product_id is required")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                f"{settings.bff_service_url}/bff/cart",
                json={"user_id": user["user_id"], "product_id": product_id, "quantity": quantity},
                headers={"Authorization": f"Bearer {body.get('token', '')}"},
            )
            if resp.status_code in (200, 201):
                return resp.json()
            raise HTTPException(status_code=502, detail="Cart service unavailable")
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="BFF service unavailable")


# ------------------------------------------------------------------
# Order endpoints (authenticated)
# ------------------------------------------------------------------


@router.post("/orders")
async def create_order(request: Request):
    """Create a new order — proxied to BFF service.

    Requires authentication via Bearer token.
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                f"{settings.bff_service_url}/bff/orders",
                json={"user_id": user["user_id"], **body},
            )
            if resp.status_code in (200, 201):
                return resp.json()
            raise HTTPException(status_code=502, detail="Order service unavailable")
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="BFF service unavailable")


@router.get("/orders/{order_id}")
async def get_order(order_id: str, request: Request):
    """Get order details — proxied to BFF service.

    Requires authentication via Bearer token.
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                f"{settings.bff_service_url}/bff/orders",
                params={"user_id": user["user_id"], "order_id": order_id},
            )
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=502, detail="Order service unavailable")
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="BFF service unavailable")
