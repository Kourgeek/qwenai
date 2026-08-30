"""FastAPI router for Admin Service HTTP endpoints."""

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from src.repositories.admin_repository import AdminRepository
from src.repositories.audit_repository import AuditRepository
from src.services.admin_service import AdminService
from src.database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


def _get_service(db=Depends(get_db)) -> AdminService:
    """Dependency that builds the ``AdminService`` with its repos."""
    return AdminService(
        admin_repo=AdminRepository(db),
        audit_repo=AuditRepository(db),
    )


# ------------------------------------------------------------------
# POST /admin/login
# ------------------------------------------------------------------
@router.post("/login")
async def admin_login(
    request: Request,
    service: AdminService = Depends(_get_service),
    x_forwarded_for: str | None = Header(default=None),
):
    body = await request.json()
    token = body.get("token", "")
    ip = x_forwarded_for or (request.client.host if request.client else None)
    try:
        result = await service.login_admin(token, ip_address=ip)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    return result


# ------------------------------------------------------------------
# GET /admin/dashboard
# ------------------------------------------------------------------
@router.get("/dashboard")
async def get_dashboard(
    service: AdminService = Depends(_get_service),
    authorization: str | None = Header(default=None),
):
    token = _extract_token(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    try:
        return await service.get_dashboard_stats(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


# ------------------------------------------------------------------
# PUT /admin/products/{product_id}/status
# ------------------------------------------------------------------
@router.put("/products/{product_id}/status")
async def update_product_status(
    product_id: str,
    request: Request,
    service: AdminService = Depends(_get_service),
    authorization: str | None = Header(default=None),
    x_forwarded_for: str | None = Header(default=None),
):
    token = _extract_token(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    body = await request.json()
    status_val = body.get("status", "").upper()
    if status_val not in ("APPROVED", "REJECTED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="status must be APPROVED or REJECTED",
        )
    ip = x_forwarded_for or (request.client.host if request.client else None)
    try:
        return await service.manage_product(token, product_id, status_val, ip_address=ip)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ------------------------------------------------------------------
# PUT /admin/sellers/{seller_id}/status
# ------------------------------------------------------------------
@router.put("/sellers/{seller_id}/status")
async def update_seller_status(
    seller_id: str,
    request: Request,
    service: AdminService = Depends(_get_service),
    authorization: str | None = Header(default=None),
    x_forwarded_for: str | None = Header(default=None),
):
    token = _extract_token(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    body = await request.json()
    status_val = body.get("status", "").upper()
    if status_val not in ("APPROVED", "REJECTED", "DEACTIVATED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="status must be APPROVED, REJECTED, or DEACTIVATED",
        )
    ip = x_forwarded_for or (request.client.host if request.client else None)
    try:
        return await service.manage_seller(token, seller_id, status_val, ip_address=ip)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ------------------------------------------------------------------
# GET /admin/audit
# ------------------------------------------------------------------
@router.get("/audit")
async def get_audit_logs(
    service: AdminService = Depends(_get_service),
    authorization: str | None = Header(default=None),
    entity_type: str | None = None,
    entity_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    token = _extract_token(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    try:
        return await service.get_audit_logs(
            token,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


# ------------------------------------------------------------------
# POST /admin/roles/assign
# ------------------------------------------------------------------
@router.post("/roles/assign")
async def assign_role(
    request: Request,
    service: AdminService = Depends(_get_service),
    authorization: str | None = Header(default=None),
    x_forwarded_for: str | None = Header(default=None),
):
    token = _extract_token(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    body = await request.json()
    admin_id = body.get("admin_id")
    role = body.get("role")
    if not admin_id or not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="admin_id and role are required",
        )
    ip = x_forwarded_for or (request.client.host if request.client else None)
    try:
        return await service.assign_role(token, admin_id, role, ip_address=ip)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _extract_token(authorization: str | None) -> str:
    """Extract the Bearer token from an ``Authorization`` header."""
    if not authorization:
        return ""
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return ""
