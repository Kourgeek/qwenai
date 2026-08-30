"""Tests for SellerService business logic."""

import uuid

import pytest

from src.repositories import seller_repository
from src.services.seller_service import SellerNotFoundError, SellerValidationError, SellerService


# ------------------------------------------------------------------
# register_seller
# ------------------------------------------------------------------

class TestRegisterSeller:
    """Tests for SellerService.register_seller."""

    @pytest.mark.asyncio
    async def test_register_seller_success(self, seller_service: SellerService, db_session):
        """Should create a seller with PENDING status."""
        user_id = uuid.uuid4()
        result = await seller_service.register_seller(
            session=db_session,
            user_id=user_id,
            company_name="Test Corp",
            inn="123456789012",
            kpp="123456789",
        )
        assert result["company_name"] == "Test Corp"
        assert result["inn"] == "123456789012"
        assert result["status"] == "PENDING"
        assert "id" in result

    @pytest.mark.asyncio
    async def test_register_seller_missing_company_name(self, seller_service: SellerService, db_session):
        """Should raise SellerValidationError when company_name is empty."""
        with pytest.raises(SellerValidationError, match="company_name is required"):
            await seller_service.register_seller(
                session=db_session,
                user_id=uuid.uuid4(),
                company_name="",
                inn="123456789012",
            )

    @pytest.mark.asyncio
    async def test_register_seller_missing_inn(self, seller_service: SellerService, db_session):
        """Should raise SellerValidationError when inn is empty."""
        with pytest.raises(SellerValidationError, match="inn is required"):
            await seller_service.register_seller(
                session=db_session,
                user_id=uuid.uuid4(),
                company_name="Test Corp",
                inn="",
            )

    @pytest.mark.asyncio
    async def test_register_seller_invalid_inn_length(self, seller_service: SellerService, db_session):
        """Should raise SellerValidationError when inn is not 12 digits."""
        with pytest.raises(SellerValidationError, match="inn must be exactly 12 digits"):
            await seller_service.register_seller(
                session=db_session,
                user_id=uuid.uuid4(),
                company_name="Test Corp",
                inn="12345",
            )

    @pytest.mark.asyncio
    async def test_register_seller_duplicate_inn(self, seller_service: SellerService, db_session):
        """Should raise SellerValidationError on duplicate INN."""
        inn = "123456789012"
        await seller_service.register_seller(
            session=db_session,
            user_id=uuid.uuid4(),
            company_name="First Corp",
            inn=inn,
        )
        with pytest.raises(SellerValidationError, match="A seller with this INN already exists"):
            await seller_service.register_seller(
                session=db_session,
                user_id=uuid.uuid4(),
                company_name="Second Corp",
                inn=inn,
            )


# ------------------------------------------------------------------
# get_seller
# ------------------------------------------------------------------

class TestGetSeller:
    """Tests for SellerService.get_seller."""

    @pytest.mark.asyncio
    async def test_get_seller_success(self, seller_service: SellerService, db_session, test_seller):
        """Should return seller data for an existing ID."""
        result = await seller_service.get_seller(db_session, test_seller)
        assert result["id"] == str(test_seller)
        assert result["company_name"] == "Test Corp"
        assert result["status"] == "APPROVED"

    @pytest.mark.asyncio
    async def test_get_seller_not_found(self, seller_service: SellerService, db_session):
        """Should raise SellerNotFoundError for non-existent ID."""
        fake_id = uuid.uuid4()
        with pytest.raises(SellerNotFoundError, match="Seller not found"):
            await seller_service.get_seller(db_session, fake_id)


# ------------------------------------------------------------------
# update_seller
# ------------------------------------------------------------------

class TestUpdateSeller:
    """Tests for SellerService.update_seller."""

    @pytest.mark.asyncio
    async def test_update_seller_success(self, seller_service: SellerService, db_session, test_seller):
        """Should update company_name and return updated data."""
        result = await seller_service.update_seller(
            db_session,
            test_seller,
            company_name="Updated Corp",
        )
        assert result["company_name"] == "Updated Corp"
        assert result["id"] == str(test_seller)

    @pytest.mark.asyncio
    async def test_update_seller_no_valid_fields(self, seller_service: SellerService, db_session, test_seller):
        """Should raise SellerValidationError when no valid fields are provided."""
        with pytest.raises(SellerValidationError, match="No valid fields to update"):
            await seller_service.update_seller(
                db_session,
                test_seller,
                invalid_field="value",
            )

    @pytest.mark.asyncio
    async def test_update_seller_not_found(self, seller_service: SellerService, db_session):
        """Should raise SellerNotFoundError for non-existent ID."""
        fake_id = uuid.uuid4()
        with pytest.raises(SellerNotFoundError, match="Seller not found"):
            await seller_service.update_seller(db_session, fake_id, company_name="X")


# ------------------------------------------------------------------
# get_seller_products
# ------------------------------------------------------------------

class TestGetSellerProducts:
    """Tests for SellerService.get_seller_products."""

    @pytest.mark.asyncio
    async def test_get_seller_products_empty(self, seller_service: SellerService):
        """Should return empty list when no products exist."""
        result = await seller_service.get_seller_products(uuid.uuid4())
        assert result == []

    @pytest.mark.asyncio
    async def test_get_seller_products_with_data(self, seller_service: SellerService, test_seller):
        """Should return products from catalog client."""
        result = await seller_service.get_seller_products(test_seller)
        assert len(result) == 2  # from mock
        assert result[0]["name"] == "Product A"
