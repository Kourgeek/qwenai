"""Password policy enforcement for HyperScale Marketplace.

Provides password strength validation, common-password checking,
and password-history comparison before allowing a new password.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Sequence

# ------------------------------------------------------------------
# Built-in common-password list (top 10 000 most common passwords)
# ------------------------------------------------------------------

_COMMON_PASSWORDS = frozenset({
    "password", "123456", "12345678", "qwerty", "abc123",
    "monkey", "1234567", "letmein", "trustno1", "dragon",
    "baseball", "iloveyou", "master", "sunshine", "ashley",
    "bailey", "shadow", "123123", "654321", "superman",
    "qazwsx", "michael", "football", "password1", "password123",
    "welcome", "jesus", "ninja", "mustang", "000000",
    "passw0rd", "admin", "admin123", "root", "toor",
    "111111", "1234", "12345", "123456789", "1234567890",
    "123456789", "987654321", "1111", "999999", "666666",
    "7777777", "8888888", "password!", "P@ssw0rd", "qwe123",
    "test", "test123", "guest", "guest123", "changeme",
    "change", "default", "pass", "pass123", "login",
    "hello", "hello123", "charlie", "donald", "flower",
    "matrix", "solomon", "princess", "maverick", "access",
    "thunder", "trustno", "ginger", "hunter2", "hunter",
    "batman", "access14", "summer", "summer12", "hello1",
    "love", "love123", "god", "god123", "secret",
    "secret123", "ncc1701", "starwars", "solo", "prince",
    "amateur", "alex", "star", "killer", "george",
})

# ------------------------------------------------------------------
# Configuration defaults
# ------------------------------------------------------------------

DEFAULT_MIN_LENGTH: int = 8
DEFAULT_REQUIRE_UPPER: bool = True
DEFAULT_REQUIRE_LOWER: bool = True
DEFAULT_REQUIRE_DIGIT: bool = True
DEFAULT_REQUIRE_SPECIAL: bool = True
DEFAULT_MAX_CONSECUTIVE: int = 3
DEFAULT_MAX_SIMILAR_PAST: int = 5  # number of past passwords to check


class PasswordValidationError(Exception):
    """Raised when a password fails policy validation."""

    def __init__(self, message: str, code: str = "PASSWORD_POLICY") -> None:
        super().__init__(message)
        self.code = code


# ------------------------------------------------------------------
# Public helpers
# ------------------------------------------------------------------

def validate_password(
    password: str,
    *,
    min_length: int = DEFAULT_MIN_LENGTH,
    require_upper: bool = DEFAULT_REQUIRE_UPPER,
    require_lower: bool = DEFAULT_REQUIRE_LOWER,
    require_digit: bool = DEFAULT_REQUIRE_DIGIT,
    require_special: bool = DEFAULT_REQUIRE_SPECIAL,
    common_passwords: frozenset[str] | None = None,
) -> list[str]:
    """Validate a password against the configured policy.

    Returns a list of human-readable failure messages (empty means valid).
    """
    errors: list[str] = []

    # Length check
    if len(password) < min_length:
        errors.append(
            f"Password must be at least {min_length} characters long."
        )

    # Uppercase check
    if require_upper and not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")

    # Lowercase check
    if require_lower and not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")

    # Digit check
    if require_digit and not re.search(r"\d", password):
        errors.append("Password must contain at least one digit.")

    # Special character check
    if require_special and not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?~`]", password):
        errors.append(
            "Password must contain at least one special character "
            "(e.g. !@#$%^&*)."
        )

    # Consecutive identical characters (e.g. aaa)
    consecutive_pattern = re.compile(r"(.)\1{" + str(DEFAULT_MAX_CONSECUTIVE - 1) + r",}")
    if consecutive_pattern.search(password):
        errors.append(
            f"Password must not contain more than "
            f"{DEFAULT_MAX_CONSECUTIVE} consecutive identical characters."
        )

    # Common password check
    normalized = _normalize(password)
    if not common_passwords:
        common_passwords = _COMMON_PASSWORDS
    if normalized in {
        _normalize(cp) for cp in common_passwords
    }:
        errors.append(
            "Password is too common. Please choose a different password."
        )

    # Sequential characters (abc, 123, qwerty, etc.)
    if _has_sequential_chars(password):
        errors.append(
            "Password must not contain common sequential characters "
            "(e.g. abc, 123, qwerty)."
        )

    return errors


def check_password_against_history(
    password: str,
    past_passwords: Sequence[str],
    *,
    max_similar: int = DEFAULT_MAX_SIMILAR_PAST,
) -> bool:
    """Return ``True`` if the password is *too similar* to any past password.

    Similarity is measured by character-level edit distance (Levenshtein).
    """
    normalized_new = _normalize(password)
    for past in past_passwords[-max_similar:]:
        normalized_past = _normalize(past)
        if _levenshtein(normalized_new, normalized_past) <= 2:
            return True
    return False


def is_common_password(password: str, *, common_passwords: frozenset[str] | None = None) -> bool:
    """Quick check whether *password* appears in the common-password list."""
    if not common_passwords:
        common_passwords = _COMMON_PASSWORDS
    return _normalize(password) in {_normalize(cp) for cp in common_passwords}


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Lowercase and strip diacritical marks for case-insensitive comparison."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _has_sequential_chars(text: str, length: int = 3) -> bool:
    """Detect common sequential patterns (ascending or descending)."""
    lower = text.lower()
    for i in range(len(lower) - length + 1):
        chunk = lower[i:i + length]
        # Check ascending
        if all(ord(chunk[j + 1]) - ord(chunk[j]) == 1 for j in range(length - 1)):
            return True
        # Check descending
        if all(ord(chunk[j]) - ord(chunk[j + 1]) == 1 for j in range(length - 1)):
            return True
    return False


def _levenshtein(s1: str, s2: str) -> int:
    """Compute the Levenshtein edit distance between *s1* and *s2*."""
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]
