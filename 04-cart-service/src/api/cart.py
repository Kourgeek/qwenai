"""FastAPI router for cart HTTP endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from src.services.cart_service import cart_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cart", tags=["cart"])


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _extract_user_id(request: Request) -> str:
    """Derive user_id from the Authorization header.

    In production this would decode the JWT and extract the subject.
    For now we read a simple header set by the API gateway.
    """
    user_id = request.headers.get("x-user-id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing x-user-id header",
        )
    return user_id


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.get("", response_model=dict[str, Any])
async def get_cart(request: Request) -> dict[str, Any]:
    """Retrieve the current shopping cart for the authenticated user."""
    user_id = _extract_user_id(request)
    try:
        return await cart_service.get_cart(user_id)
    except Exception as exc:
        logger.error("GetCart error user=%s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/items", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
async def add_item(request: Request, product_id: str, quantity: int = 1) -> dict[str, Any]:
    """Add *quantity* of *product_id* to the cart."""
    user_id = _extract_user_id(request)
    try:
        return await cart_service.add_item(user_id, product_id, quantity)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("AddItem error user=%s product=%s: %s", user_id, product_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.put("/items/{product_id}", response_model=dict[str, Any])
async def update_item(request: Request, product_id: str, quantity: int) -> dict[str, Any]:
    """Update the quantity of *product_id* in the cart."""
    user_id = _extract_user_id(request)
    try:
        return await cart_service.update_item(user_id, product_id, quantity)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("UpdateItem error user=%s product=%s: %s", user_id, product_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/items/{product_id}", response_model=dict[str, Any])
async def remove_item(request: Request, product_id: str) -> dict[str, Any]:
    """Remove *product_id* from the cart."""
    user_id = _extract_user_id(request)
    try:
        return await cart_service.remove_item(user_id, product_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("RemoveItem error user=%s product=%s: %s", user_id, product_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/clear", response_model=dict[str, Any])
async def clear_cart(request: Request) -> dict[str, Any]:
    """Clear all items from the cart."""
    user_id = _extract_user_id(request)
    try:
        return await cart_service.clear_cart(user_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("ClearCart error user=%s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/save-for-later", response_model=dict[str, Any])
async def save_for_later(request: Request, product_id: str) -> dict[str, Any]:
    """Move *product_id* from cart to the saved-for-later list."""
    user_id = _extract_user_id(request)
    try:
        return await cart_service.save_for_later(user_id, product_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("SaveForLater error user=%s product=%s: %s", user_id, product_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/move-to-cart", response_model=dict[str, Any])
async def move_to_cart(request: Request, product_id: str) -> dict[str, Any]:
    """Move *product_id* from saved-for-later back to cart."""
    user_id = _extract_user_id(request)
    try:
        return await cart_service.move_to_cart(user_id, product_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("MoveToCart error user=%s product=%s: %s", user_id, product_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
