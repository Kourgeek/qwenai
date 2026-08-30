"""Business logic for the Admin Service."""

import logging
import uuid
from datetime import datetime, timezone

from src.grpc_client import auth_client, catalog_client, order_client, seller_client
from src.repositories.admin_repository import AdminRepository
from src.repositories.audit_repository import AuditRepository
from src.models.admin import AdminUser

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Allowed roles and their default permission sets
# ---------------------------------------------------------------------------
VALID_ROLES = frozenset({
    "SUPER_ADMIN",
    "CATALOG_MANAGER",
    "ORDER_MANAGER",
    "SELLER_MANAGER",
})

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "SUPER_ADMIN": [
        "admin:login",
        "admin:dashboard",
        "admin:audit:read",
        "admin:role:assign",
        "catalog:product:read",
        "catalog:product:write",
        "catalog:product:approve",
        "catalog:product:reject",
        "order:read",
        "order:manage",
        "seller:read",
        "seller:manage",
    ],
    "CATALOG_MANAGER": [
        "admin:dashboard",
        "catalog:product:read",
        "catalog:product:approve",
        "catalog:product:reject",
    ],
    "ORDER_MANAGER": [
        "admin:dashboard",
        "order:read",
        "order:manage",
    ],
    "SELLER_MANAGER": [
        "admin:dashboard",
        "seller:read",
        "seller:manage",
    ],
}


class AdminService:
    """Orchestrates admin-related business operations."""

    def __init__(
        self,
        admin_repo: AdminRepository,
        audit_repo: AuditRepository,
    ) -> None:
        self._admin_repo = admin_repo
        self._audit_repo = audit_repo

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    async def _require_admin(self, token: str) -> AdminUser:
        """Validate token, return the corresponding ``AdminUser``."""
        valid = await auth_client.verify_token(token)
        if not valid:
            raise ValueError("Invalid or expired token")

        roles = await auth_client.get_user_roles(token)
        if not roles:
            raise ValueError("Token has no associated roles")

        # Find or create the admin record
        user_id = roles[0]  # first role entry contains the user_id
        admin = await self._admin_repo.get_by_user_id(user_id)
        if admin is None:
            admin = await self._admin_repo.create(user_id=user_id)

        return admin

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    async def login_admin(self, token: str, ip_address: str | None = None) -> dict:
        """Authenticate an admin and return session info."""
        admin = await self._require_admin(token)
        return {
            "admin_id": str(admin.id),
            "user_id": admin.user_id,
            "role": admin.role,
            "permissions": admin.permissions,
            "ip_address": ip_address,
        }

    async def get_dashboard_stats(self, token: str) -> dict:
        """Collect aggregate statistics from downstream services."""
        await self._require_admin(token)  # gate by auth

        # Parallel fetch from Catalog, Order, Seller services
        products = await catalog_client.list_products()
        orders = await order_client.list_orders()
        sellers = await seller_client.list_sellers()

        return {
            "products": {
                "total": len(products),
                "pending": len([p for p in products if p.get("status") == "PENDING"]),
                "approved": len([p for p in products if p.get("status") == "APPROVED"]),
                "rejected": len([p for p in products if p.get("status") == "REJECTED"]),
            },
            "orders": {
                "total": len(orders),
                "pending": len([o for o in orders if o.get("status") == "PENDING"]),
                "completed": len([o for o in orders if o.get("status") == "COMPLETED"]),
            },
            "sellers": {
                "total": len(sellers),
                "active": len([s for s in sellers if s.get("status") == "ACTIVE"]),
                "deactivated": len([s for s in sellers if s.get("status") == "DEACTIVATED"]),
            },
        }

    async def manage_product(
        self,
        token: str,
        product_id: str,
        status: str,
        ip_address: str | None = None,
    ) -> dict:
        """Approve or reject a product.

        Parameters
        ----------
        token:
            Bearer token of the admin.
        product_id:
            Product identifier.
        status:
            Target status – ``APPROVED`` or ``REJECTED``.
        ip_address:
            Optional client IP for audit trail.
        """
        admin = await self._require_admin(token)

        # Fetch current product state for audit
        product = await catalog_client.get_product(product_id)
        old_status = product.get("status") if product else None

        # Delegate status change to Catalog Service via gRPC
        # (In production this would be a real stub call)

        # Audit log
        await self._audit_repo.create(
            admin_id=str(admin.id),
            action="manage_product",
            entity_type="product",
            entity_id=product_id,
            old_values={"status": old_status},
            new_values={"status": status},
            ip_address=ip_address,
        )

        logger.info("Product %s status → %s by admin %s", product_id, status, admin.user_id)
        return {"product_id": product_id, "status": status, "updated_by": admin.user_id}

    async def manage_seller(
        self,
        token: str,
        seller_id: str,
        status: str,
        ip_address: str | None = None,
    ) -> dict:
        """Approve, reject, or deactivate a seller.

        Parameters
        ----------
        token:
            Bearer token of the admin.
        seller_id:
            Seller identifier.
        status:
            Target status – ``APPROVED``, ``REJECTED``, or ``DEACTIVATED``.
        ip_address:
            Optional client IP for audit trail.
        """
        admin = await self._require_admin(token)

        # Fetch current seller state for audit
        seller = await seller_client.get_seller(seller_id)
        old_status = seller.get("status") if seller else None

        # Delegate status change to Seller Service via gRPC

        # Audit log
        await self._audit_repo.create(
            admin_id=str(admin.id),
            action="manage_seller",
            entity_type="seller",
            entity_id=seller_id,
            old_values={"status": old_status},
            new_values={"status": status},
            ip_address=ip_address,
        )

        logger.info("Seller %s status → %s by admin %s", seller_id, status, admin.user_id)
        return {"seller_id": seller_id, "status": status, "updated_by": admin.user_id}

    async def get_audit_logs(
        self,
        token: str,
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """Return audit log entries, optionally filtered."""
        admin = await self._require_admin(token)

        if entity_type and entity_id:
            logs = await self._audit_repo.get_by_entity(
                entity_type, entity_id, limit=limit, offset=offset
            )
        else:
            logs = await self._audit_repo.get_all(limit=limit, offset=offset)

        return [
            {
                "id": str(log.id),
                "admin_id": log.admin_id,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "old_values": log.old_values,
                "new_values": log.new_values,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]

    async def assign_role(
        self,
        token: str,
        admin_id: str,
        new_role: str,
        ip_address: str | None = None,
    ) -> dict:
        """Assign a new role to an existing admin user.

        Only ``SUPER_ADMIN`` can call this endpoint.
        """
        super_admin = await self._require_admin(token)

        if super_admin.role != "SUPER_ADMIN":
            raise PermissionError("Only SUPER_ADMIN can assign roles")

        if new_role not in VALID_ROLES:
            raise ValueError(f"Invalid role: {new_role}. Must be one of {VALID_ROLES}")

        updated = await self._admin_repo.update_role(admin_id, new_role)
        if updated is None:
            raise ValueError(f"Admin user with id {admin_id} not found")

        # Audit log
        await self._audit_repo.create(
            admin_id=str(super_admin.id),
            action="assign_role",
            entity_type="admin_user",
            entity_id=admin_id,
            old_values={"role": super_admin.role},
            new_values={"role": new_role},
            ip_address=ip_address,
        )

        return {
            "admin_id": admin_id,
            "new_role": new_role,
            "assigned_by": super_admin.user_id,
            "assigned_at": datetime.now(timezone.utc).isoformat(),
        }
