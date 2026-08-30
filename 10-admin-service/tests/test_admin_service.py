"""Tests for AdminService business logic."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock

from src.models.admin import AdminUser
from src.services.admin_service import AdminService


# ------------------------------------------------------------------
# login_admin
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_admin_success(admin_service: AdminService) -> None:
    """Valid token should return admin session info."""
    result = await admin_service.login_admin("valid-token-xyz")
    assert result["admin_id"] is not None
    assert result["role"] == "CATALOG_MANAGER"
    assert result["permissions"] == {}


@pytest.mark.asyncio
async def test_login_admin_invalid_token(admin_service: AdminService) -> None:
    """Invalid token should raise ValueError."""
    admin_service._require_admin = AsyncMock(side_effect=ValueError("Invalid or expired token"))  # type: ignore[attr-defined]
    with pytest.raises(ValueError, match="Invalid or expired token"):
        await admin_service.login_admin("bad-token")


# ------------------------------------------------------------------
# get_dashboard_stats
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_dashboard_stats(admin_service: AdminService, mock_catalog_client: MagicMock, mock_order_client: MagicMock, mock_seller_client: MagicMock) -> None:
    """Dashboard should return aggregated stats from downstream services."""
    result = await admin_service.get_dashboard_stats("valid-token")
    assert "products" in result
    assert "orders" in result
    assert "sellers" in result
    assert result["products"]["total"] == 2
    assert result["orders"]["total"] == 2
    assert result["sellers"]["total"] == 2


# ------------------------------------------------------------------
# manage_product
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_manage_product_approve(admin_service: AdminService, test_admin_user: AdminUser, mock_catalog_client: MagicMock) -> None:
    """Approving a product should update status and create audit log."""
    result = await admin_service.manage_product(
        "valid-token",
        "product-1",
        "APPROVED",
        ip_address="127.0.0.1",
    )
    assert result["product_id"] == "product-1"
    assert result["status"] == "APPROVED"


@pytest.mark.asyncio
async def test_manage_product_reject(admin_service: AdminService) -> None:
    """Rejecting a product should update status and create audit log."""
    result = await admin_service.manage_product(
        "valid-token",
        "product-2",
        "REJECTED",
        ip_address="127.0.0.1",
    )
    assert result["product_id"] == "product-2"
    assert result["status"] == "REJECTED"


# ------------------------------------------------------------------
# manage_seller
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_manage_seller_deactivate(admin_service: AdminService, mock_seller_client: MagicMock) -> None:
    """Deactivating a seller should update status and create audit log."""
    result = await admin_service.manage_seller(
        "valid-token",
        "seller-1",
        "DEACTIVATED",
        ip_address="127.0.0.1",
    )
    assert result["seller_id"] == "seller-1"
    assert result["status"] == "DEACTIVATED"


@pytest.mark.asyncio
async def test_manage_seller_approve(admin_service: AdminService) -> None:
    """Approving a seller should update status and create audit log."""
    result = await admin_service.manage_seller(
        "valid-token",
        "seller-2",
        "APPROVED",
        ip_address="127.0.0.1",
    )
    assert result["seller_id"] == "seller-2"
    assert result["status"] == "APPROVED"


# ------------------------------------------------------------------
# assign_role
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_assign_role_super_admin(admin_service: AdminService, test_admin_user: AdminUser) -> None:
    """SUPER_ADMIN should be able to assign roles."""
    result = await admin_service.assign_role(
        "valid-token",
        str(test_admin_user.id),
        "CATALOG_MANAGER",
        ip_address="127.0.0.1",
    )
    assert result["new_role"] == "CATALOG_MANAGER"
    assert result["assigned_by"] == test_admin_user.user_id


@pytest.mark.asyncio
async def test_assign_role_non_super_admin(admin_service: AdminService, monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-SUPER_ADMIN should be denied."""
    # Simulate a non-super-admin admin user
    admin_service._require_admin = AsyncMock(return_value=AdminUser(
        user_id="user-002",
        role="CATALOG_MANAGER",
        permissions=["catalog:*"],
    ))
    with pytest.raises(PermissionError, match="Only SUPER_ADMIN"):
        await admin_service.assign_role(
            "valid-token",
            "some-admin-id",
            "SUPER_ADMIN",
        )


# ------------------------------------------------------------------
# get_audit_logs
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_audit_logs(admin_service: AdminService) -> None:
    """Audit logs should be retrievable."""
    result = await admin_service.get_audit_logs("valid-token")
    assert isinstance(result, list)
