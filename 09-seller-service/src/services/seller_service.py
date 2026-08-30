"""Service layer: business logic for the Seller domain."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.grpc_client.auth_client import verify_token
from src.grpc_client.catalog_client import get_product, list_products_by_seller
from src.grpc_client.order_client import get_seller_orders
from src.repositories import seller_product_repository as sp_repo
from src.repositories import seller_repository as repo

logger = logging.getLogger(__name__)

# Valid seller statuses
VALID_STATUSES = {"PENDING", "APPROVED", "REJECTED", "DEACTIVATED"}


class SellerNotFoundError(Exception):
    """Raised when a requested seller does not exist."""


class SellerValidationError(Exception):
    """Raised when seller input validation fails."""


class SellerService:
    """Encapsulates seller business rules."""

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    async def register_seller(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        company_name: str,
        inn: str,
        kpp: str | None = None,
        bank_name: str | None = None,
        bank_account: str | None = None,
        bank_bik: str | None = None,
        token: str | None = None,
    ) -> dict:
        """Register a new seller.

        Validates token (if provided), checks for duplicate INN, and
        creates the seller with status PENDING.
        """
        # 1. Token verification (optional but recommended)
        if token:
            valid = await verify_token(token)
            if not valid:
                raise SellerValidationError("Invalid or expired authentication token")

        # 2. Business validation
        if not company_name or not company_name.strip():
            raise SellerValidationError("company_name is required")
        if not inn or not inn.strip():
            raise SellerValidationError("inn is required")
        if len(inn) != 12:
            raise SellerValidationError("inn must be exactly 12 digits")

        # 3. Check duplicate INN
        existing = await repo.get_seller_by_inn(session, inn.strip())
        if existing and existing.status != "DEACTIVATED":
            raise SellerValidationError("A seller with this INN already exists")

        # 4. Check duplicate user_id
        existing_user = await repo.get_seller_by_user_id(session, user_id)
        if existing_user and existing_user.status != "DEACTIVATED":
            raise SellerValidationError("A seller is already registered for this user")

        # 5. Create seller record
        seller = await repo.create_seller(
            session=session,
            user_id=user_id,
            company_name=company_name.strip(),
            inn=inn.strip(),
            kpp=kpp,
            bank_name=bank_name,
            bank_account=bank_account,
            bank_bik=bank_bik,
            status="PENDING",
        )

        logger.info("Seller registered: id=%s, company=%s", seller.id, seller.company_name)
        return self._seller_to_dict(seller)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    async def get_seller(self, session: AsyncSession, seller_id: uuid.UUID) -> dict:
        """Fetch a seller by ID."""
        seller = await repo.get_seller_by_id(session, seller_id)
        if not seller:
            raise SellerNotFoundError(f"Seller not found: {seller_id}")
        return self._seller_to_dict(seller)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update_seller(
        self,
        session: AsyncSession,
        seller_id: uuid.UUID,
        token: str | None = None,
        **fields,
    ) -> dict:
        """Update seller fields. Only mutable fields are accepted."""
        if token:
            valid = await verify_token(token)
            if not valid:
                raise SellerValidationError("Invalid or expired authentication token")

        seller = await repo.get_seller_by_id(session, seller_id)
        if not seller:
            raise SellerNotFoundError(f"Seller not found: {seller_id}")

        if seller.status == "DEACTIVATED":
            raise SellerValidationError("Cannot update a deactivated seller")

        allowed_fields = {"company_name", "kpp", "bank_name", "bank_account", "bank_bik"}
        filtered = {k: v for k, v in fields.items() if k in allowed_fields and v is not None}

        if not filtered:
            raise SellerValidationError("No valid fields to update")

        updated = await repo.update_seller(session, seller, **filtered)
        logger.info("Seller updated: id=%s", updated.id)
        return self._seller_to_dict(updated)

    # ------------------------------------------------------------------
    # Products
    # ------------------------------------------------------------------

    async def get_seller_products(self, seller_id: uuid.UUID) -> list[dict]:
        """Fetch product mappings from Catalog service for this seller."""
        products = await list_products_by_seller(str(seller_id))
        return products

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    async def get_seller_orders(
        self,
        seller_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """Fetch paginated orders from the Order service for this seller."""
        orders = await get_seller_orders(str(seller_id), page=page, page_size=page_size)
        return orders

    # ------------------------------------------------------------------
    # Deactivation
    # ------------------------------------------------------------------

    async def deactivate_seller(
        self,
        session: AsyncSession,
        seller_id: uuid.UUID,
        token: str | None = None,
    ) -> dict:
        """Deactivate a seller (soft-delete)."""
        if token:
            valid = await verify_token(token)
            if not valid:
                raise SellerValidationError("Invalid or expired authentication token")

        seller = await repo.get_seller_by_id(session, seller_id)
        if not seller:
            raise SellerNotFoundError(f"Seller not found: {seller_id}")

        if seller.status == "DEACTIVATED":
            raise SellerValidationError("Seller is already deactivated")

        seller.status = "DEACTIVATED"
        await session.flush()
        logger.info("Seller deactivated: id=%s", seller_id)
        return self._seller_to_dict(seller)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _seller_to_dict(seller) -> dict:
        """Convert a Seller ORM instance to a plain dict."""
        return {
            "id": str(seller.id),
            "user_id": str(seller.user_id),
            "company_name": seller.company_name,
            "inn": seller.inn,
            "kpp": seller.kpp,
            "bank_name": seller.bank_name,
            "bank_account": seller.bank_account,
            "bank_bik": seller.bank_bik,
            "status": seller.status,
            "created_at": seller.created_at.isoformat() if seller.created_at else None,
            "updated_at": seller.updated_at.isoformat() if seller.updated_at else None,
        }
