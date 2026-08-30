"""Password hashing, validation, and random secret generation.

Integrates with the security module's password policy for pre-hash
validation and uses bcrypt for secure password hashing.
"""

from __future__ import annotations

import secrets
import logging
from typing import Sequence

import bcrypt

from security.password_policy import (
    validate_password,
    check_password_against_history,
    is_common_password,
    PasswordValidationError,
)

logger = logging.getLogger(__name__)


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain*."""
    # Truncate to 72 bytes as required by bcrypt
    if len(plain.encode("utf-8")) > 72:
        plain = plain[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify *plain* against *hashed*; returns ``True`` on match."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def validate_password_strength(
    password: str,
    past_passwords: Sequence[str] = (),
    *,
    min_length: int = 8,
    require_upper: bool = True,
    require_lower: bool = True,
    require_digit: bool = True,
    require_special: bool = True,
) -> list[str]:
    """Validate a password against the full policy.

    Returns a list of human-readable failure messages.
    Empty list means the password is acceptable.
    """
    errors = validate_password(
        password,
        min_length=min_length,
        require_upper=require_upper,
        require_lower=require_lower,
        require_digit=require_digit,
        require_special=require_special,
    )

    # Check against past passwords
    if past_passwords and check_password_against_history(password, past_passwords):
        errors.append(
            "Password is too similar to a previously used password."
        )

    return errors


def generate_token(length: int = 32) -> str:
    """Return a URL-safe random string suitable for refresh tokens."""
    return secrets.token_urlsafe(length)


def generate_secure_token(length: int = 32) -> str:
    """Alias for generate_token — cryptographically secure."""
    return generate_token(length)
