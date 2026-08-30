"""FastAPI router for Seller REST endpoints."""

import logging

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from src.database import get_db
from src.services.seller_service import SellerNotFoundError, SellerValidationError
from src.services.seller_service import SellerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sellers", tags=["sellers"])

_service = SellerService()


def _get_service() -> SellerService:
    return _service


# ------------------------------------------------------------------
# POST /sellers/register
# ------------------------------------------------------------------

@router.post(
    "/register",
    status_code=201,
    responses={
        201: {"description": "Seller registered successfully"},
        400: {"description": "Validation error"},
        401: {"description": "Authentication failed"},
    },
)
async def register_seller(
    body: dict,
    service: SellerService = Depends(_get_service),
    db=Depends(get_db),
):
    """Register a new seller."""
    try:
        result = await service.register_seller(
            session=db,
            user_id=uuid.UUID(body["user_id"]),
            company_name=body["company_name"],
            inn=body["inn"],
            kpp=body.get("kpp"),
            bank_name=body.get("bank_name"),
            bank_account=body.get("bank_account"),
            bank_bik=body.get("bank_bik"),
            token=body.get("token"),
        )
        return result
    except (SellerValidationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error registering seller")
        raise HTTPException(status_code=500, detail="Internal server error")


# ------------------------------------------------------------------
# GET /sellers/{id}
# ------------------------------------------------------------------

@router.get(
    "/{seller_id}",
    responses={
        200: {"description": "Seller retrieved successfully"},
        404: {"description": "Seller not found"},
    },
)
async def get_seller(
    seller_id: uuid.UUID,
    service: SellerService = Depends(_get_service),
    db=Depends(get_db),
):
    """Fetch a seller by ID."""
    try:
        return await service.get_seller(db, seller_id)
    except SellerNotFoundError:
        raise HTTPException(status_code=404, detail="Seller not found")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error fetching seller")
        raise HTTPException(status_code=500, detail="Internal server error")


# ------------------------------------------------------------------
# PUT /sellers/{id}
# ------------------------------------------------------------------

@router.put(
    "/{seller_id}",
    responses={
        200: {"description": "Seller updated successfully"},
        400: {"description": "Validation error"},
        404: {"description": "Seller not found"},
    },
)
async def update_seller(
    seller_id: uuid.UUID,
    body: dict,
    service: SellerService = Depends(_get_service),
    db=Depends(get_db),
):
    """Update seller fields."""
    try:
        result = await service.update_seller(
            db,
            seller_id,
            token=body.get("token"),
            company_name=body.get("company_name"),
            kpp=body.get("kpp"),
            bank_name=body.get("bank_name"),
            bank_account=body.get("bank_account"),
            bank_bik=body.get("bank_bik"),
        )
        return result
    except (SellerValidationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except SellerNotFoundError:
        raise HTTPException(status_code=404, detail="Seller not found")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error updating seller")
        raise HTTPException(status_code=500, detail="Internal server error")


# ------------------------------------------------------------------
# GET /sellers/{id}/products
# ------------------------------------------------------------------

@router.get(
    "/{seller_id}/products",
    responses={200: {"description": "Products retrieved successfully"}},
)
async def get_seller_products(
    seller_id: uuid.UUID,
    service: SellerService = Depends(_get_service),
):
    """Fetch products for a seller from the Catalog service."""
    try:
        return await service.get_seller_products(seller_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error fetching seller products")
        raise HTTPException(status_code=500, detail="Internal server error")


# ------------------------------------------------------------------
# GET /sellers/{id}/orders
# ------------------------------------------------------------------

@router.get(
    "/{seller_id}/orders",
    responses={200: {"description": "Orders retrieved successfully"}},
)
async def get_seller_orders(
    seller_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: SellerService = Depends(_get_service),
):
    """Fetch paginated orders for a seller from the Order service."""
    try:
        return await service.get_seller_orders(seller_id, page=page, page_size=page_size)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error fetching seller orders")
        raise HTTPException(status_code=500, detail="Internal server error")


# ------------------------------------------------------------------
# POST /sellers/{id}/deactivate
# ------------------------------------------------------------------

@router.post(
    "/{seller_id}/deactivate",
    responses={
        200: {"description": "Seller deactivated successfully"},
        400: {"description": "Validation error"},
        404: {"description": "Seller not found"},
    },
)
async def deactivate_seller(
    seller_id: uuid.UUID,
    body: dict = {},
    service: SellerService = Depends(_get_service),
    db=Depends(get_db),
):
    """Deactivate (soft-delete) a seller."""
    try:
        result = await service.deactivate_seller(
            db,
            seller_id,
            token=body.get("token"),
        )
        return result
    except (SellerValidationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except SellerNotFoundError:
        raise HTTPException(status_code=404, detail="Seller not found")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error deactivating seller")
        raise HTTPException(status_code=500, detail="Internal server error")
