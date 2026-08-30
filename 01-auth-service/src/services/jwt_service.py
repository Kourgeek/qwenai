"""JWT token creation, verification, and rotation helpers."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from src.config import get_settings

settings = get_settings()


def create_access_token(user_id: uuid.UUID) -> str:
    """Create a short-lived access JWT."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": now + timedelta(seconds=settings.jwt_expiry),
        "iat": now,
        "jti": secrets.token_urlsafe(16),  # unique token ID
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: uuid.UUID, token_value: str) -> str:
    """Create a refresh JWT (longer-lived for convenience).

    Args:
        user_id: The user this token is for.
        token_value: The opaque token value stored in the database.
    """
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(seconds=settings.refresh_token_expiry)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": token_value,
        "exp": expiry,
        "iat": now,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT; returns the payload dict."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def verify_token(token: str) -> tuple[dict, str | None]:
    """Verify a JWT and return ``(payload, error)``.

    On success *error* is ``None``.  On failure *payload* is ``None`` and
    *error* contains the exception message.
    """
    try:
        payload = decode_token(token)
        return payload, None
    except JWTError as exc:
        return None, str(exc)


def verify_access_token(token: str) -> tuple[dict, str | None]:
    """Verify a token is a valid *access* token.

    Returns ``(payload, error)``.
    """
    payload, error = verify_token(token)
    if error:
        return None, error
    if payload.get("type") != "access":
        return None, "Token is not an access token"
    return payload, None


def verify_refresh_token(token: str) -> tuple[dict, str | None]:
    """Verify a token is a valid *refresh* token.

    Returns ``(payload, error)``.
    """
    payload, error = verify_token(token)
    if error:
        return None, error
    if payload.get("type") != "refresh":
        return None, "Token is not a refresh token"
    return payload, None


def generate_secure_refresh_token() -> str:
    """Generate a cryptographically secure opaque refresh token value.

    This value is stored in the database and embedded in the refresh JWT.
    """
    return secrets.token_urlsafe(64)
