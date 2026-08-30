"""Core authentication business logic: register, login, refresh, logout."""

from __future__ import annotations

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from src.config import get_settings
from src.models.user import User
from src.repositories.auth_repository import AuthRepository
from src.services.jwt_service import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    generate_secure_refresh_token,
)
from src.services.password_service import (
    hash_password,
    verify_password,
    validate_password_strength,
)

logger = logging.getLogger(__name__)
settings = get_settings()


# ------------------------------------------------------------------
# Exceptions
# ------------------------------------------------------------------

class AuthServiceError(Exception):
    """Base exception for auth-service business errors."""


class UserAlreadyExistsError(AuthServiceError):
    pass


class InvalidCredentialsError(AuthServiceError):
    pass


class TokenExpiredError(AuthServiceError):
    pass


class InvalidTokenError(AuthServiceError):
    pass


class WeakPasswordError(AuthServiceError):
    """Raised when a password fails the strength policy."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("Password does not meet the security requirements.")


# ------------------------------------------------------------------
# Auth service
# ------------------------------------------------------------------

class AuthService:
    """Stateless service orchestrating repo calls and token operations."""

    def __init__(self, repository: AuthRepository) -> None:
        self._repo = repository

    # ── Register ──────────────────────────────────────────────────────

    async def register(
        self,
        email: str,
        password: str,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> dict:
        # Validate password strength before hashing
        errors = validate_password_strength(
            password,
            min_length=settings.password_min_length,
            require_upper=settings.password_require_upper,
            require_lower=settings.password_require_lower,
            require_digit=settings.password_require_digit,
            require_special=settings.password_require_special,
        )
        if errors:
            raise WeakPasswordError(errors)

        existing = await self._repo.get_user_by_email(email)
        if existing:
            raise UserAlreadyExistsError(f"User with email '{email}' already exists")

        hashed = hash_password(password)
        user = await self._repo.create_user(
            email=email,
            hashed_password=hashed,
            first_name=first_name,
            last_name=last_name,
        )

        access_token = create_access_token(user.id)
        refresh_token_value = generate_secure_refresh_token()
        refresh_jwt = create_refresh_token(user.id, refresh_token_value)
        await self._repo.create_refresh_token(
            user_id=user.id,
            token=refresh_token_value,
            expires_at=datetime.now(timezone.utc)
            + timedelta(seconds=settings.refresh_token_expiry),
        )

        return {
            "user_id": str(user.id),
            "email": user.email,
            "access_token": access_token,
            "refresh_token": refresh_jwt,
        }

    # ── Login ─────────────────────────────────────────────────────────

    async def login(
        self,
        email: str,
        password: str,
    ) -> dict:
        user = await self._repo.get_user_by_email(email)
        if not user:
            # Perform timing attack mitigation: still hash a dummy password
            hash_password("dummy")
            raise InvalidCredentialsError("Invalid email or password")

        # Verify password
        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password")

        # Issue tokens
        access_token = create_access_token(user.id)
        refresh_token_value = generate_secure_refresh_token()
        refresh_jwt = create_refresh_token(user.id, refresh_token_value)
        await self._repo.create_refresh_token(
            user_id=user.id,
            token=refresh_token_value,
            expires_at=datetime.now(timezone.utc)
            + timedelta(seconds=settings.refresh_token_expiry),
        )

        return {
            "user_id": str(user.id),
            "email": user.email,
            "access_token": access_token,
            "refresh_token": refresh_jwt,
        }

    # ── Refresh with token rotation ───────────────────────────────────

    async def refresh(
        self,
        refresh_token_value: str,
    ) -> dict:
        payload, error = verify_refresh_token(refresh_token_value)
        if error:
            raise InvalidTokenError(f"Invalid refresh token: {error}")

        user_id = uuid.UUID(payload["sub"])
        user = await self._repo.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise InvalidTokenError("User not found or inactive")

        stored = await self._repo.get_valid_refresh_token(refresh_token_value)
        if not stored:
            raise InvalidTokenError("Refresh token not found or revoked")

        # Token rotation: revoke old token, issue new ones
        await self._repo.revoke_token(refresh_token_value)

        new_access = create_access_token(user_id)
        new_raw = generate_secure_refresh_token()
        new_refresh = create_refresh_token(user_id, new_raw)
        await self._repo.create_refresh_token(
            user_id=user_id,
            token=new_raw,
            expires_at=datetime.now(timezone.utc)
            + timedelta(seconds=settings.refresh_token_expiry),
        )

        return {"access_token": new_access, "refresh_token": new_refresh}

    # ── Logout ────────────────────────────────────────────────────────

    async def logout(
        self,
        refresh_token_value: str,
    ) -> None:
        await self._repo.revoke_token(refresh_token_value)

    async def logout_all(
        self,
        user_id: uuid.UUID,
    ) -> None:
        """Revoke all refresh tokens for a user."""
        await self._repo.revoke_all_user_tokens(user_id)

    # ── Password change ───────────────────────────────────────────────

    async def change_password(
        self,
        user_id: uuid.UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        user = await self._repo.get_user_by_id(user_id)
        if not user:
            raise InvalidCredentialsError("User not found")

        if not verify_password(current_password, user.hashed_password):
            raise InvalidCredentialsError("Current password is incorrect")

        errors = validate_password_strength(
            new_password,
            min_length=settings.password_min_length,
            require_upper=settings.password_require_upper,
            require_lower=settings.password_require_lower,
            require_digit=settings.password_require_digit,
            require_special=settings.password_require_special,
        )
        if errors:
            raise WeakPasswordError(errors)

        new_hashed = hash_password(new_password)
        user.hashed_password = new_hashed
        user.updated_at = datetime.now(timezone.utc)

    # ── Forgot Password (stub) ────────────────────────────────────────

    async def forgot_password(self, email: str) -> dict:
        user = await self._repo.get_user_by_email(email)
        if not user:
            return {"email": email, "reset_token": "dummy-reset-token"}

        reset_token = generate_secure_refresh_token()
        return {"email": email, "reset_token": reset_token}
