"""Input validation helpers for HyperScale Marketplace.

Provides sanitisation and validation for common input types:
email, phone, URL, and protection against SQL injection, XSS,
and path-traversal attacks.
"""

from __future__ import annotations

import re
import urllib.parse
from typing import Optional, Sequence

# ------------------------------------------------------------------
# Patterns
# ------------------------------------------------------------------

# RFC 5322 simplified email regex (sufficient for most cases)
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9]"
    r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)

# E.164 phone number pattern
_PHONE_RE = re.compile(r"^\+?[1-9]\d{6,14}$")

# URL pattern (http/https only)
_URL_RE = re.compile(
    r"^https?://"
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,}|"
    r"localhost|"
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"\[?[A-F0-9]*:[A-F0-9:]+\]?)"
    r"(?::\d+)?"
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)

# SQL injection patterns
_SQL_PATTERNS = [
    re.compile(r"(--|#|/\*|\*/|;)", re.IGNORECASE),
    re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|EXEC)\b)", re.IGNORECASE),
    re.compile(r"(\b(OR|AND)\b\s+\d+\s*=\s*\d+)", re.IGNORECASE),
    re.compile(r"('\s*(OR|AND)\s*')", re.IGNORECASE),
    re.compile(r"(\bEXEC\s*xp_)", re.IGNORECASE),
    re.compile(r"(\bWAITFOR\s+DELAY)", re.IGNORECASE),
    re.compile(r"(\bBENCHMARK\s*\()", re.IGNORECASE),
]

# XSS patterns
_XSS_PATTERNS = [
    re.compile(r"<\s*script[^>]*>", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"<\s*img[^>]+on\w+\s*=", re.IGNORECASE),
    re.compile(r"<\s*iframe", re.IGNORECASE),
    re.compile(r"<\s*object", re.IGNORECASE),
    re.compile(r"<\s*embed", re.IGNORECASE),
    re.compile(r"<\s*form", re.IGNORECASE),
    re.compile(r"<\s*svg[^>]*on\w+", re.IGNORECASE),
    re.compile(r"expression\s*\(", re.IGNORECASE),
    re.compile(r"url\s*\(\s*['\"]?javascript", re.IGNORECASE),
]

# Path traversal patterns
_TRAVERSAL_PATTERNS = [
    re.compile(r"\.\./"),
    re.compile(r"\.\.\\", re.IGNORECASE),
    re.compile(r"%2e%2e[%/\\]"),
    re.compile(r"%252e%252e"),
    re.compile(r"\.\.%2f", re.IGNORECASE),
    re.compile(r"\.\.%5c", re.IGNORECASE),
]


# ------------------------------------------------------------------
# Validation functions
# ------------------------------------------------------------------

class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str = "input", code: str = "VALIDATION_ERROR") -> None:
        super().__init__(message)
        self.field = field
        self.code = code


def validate_email(email: str) -> bool:
    """Return ``True`` if *email* matches the email pattern."""
    if not email or len(email) > 254:
        return False
    return _EMAIL_RE.match(email) is not None


def validate_phone(phone: str) -> bool:
    """Return ``True`` if *phone* matches E.164 format."""
    cleaned = phone.strip()
    return _PHONE_RE.match(cleaned) is not None


def validate_url(url: str) -> bool:
    """Return ``True`` if *url* is a well-formed http(s) URL."""
    if not url or len(url) > 2048:
        return False
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if not parsed.netloc:
            return False
    except Exception:
        return False
    return _URL_RE.match(url) is not None


# ------------------------------------------------------------------
# Injection / attack detection
# ------------------------------------------------------------------

def check_sql_injection(payload: str) -> list[str]:
    """Return a list of detected SQL-injection indicators in *payload*."""
    findings: list[str] = []
    for pattern in _SQL_PATTERNS:
        if pattern.search(payload):
            findings.append(f"Possible SQL injection detected: {pattern.pattern}")
    return findings


def check_xss(payload: str) -> list[str]:
    """Return a list of detected XSS indicators in *payload*."""
    findings: list[str] = []
    for pattern in _XSS_PATTERNS:
        if pattern.search(payload):
            findings.append(f"Possible XSS detected: {pattern.pattern}")
    return findings


def check_path_traversal(path: str) -> list[str]:
    """Return a list of detected path-traversal indicators in *path*."""
    findings: list[str] = []
    decoded = urllib.parse.unquote(urllib.parse.unquote(path))
    for pattern in _TRAVERSAL_PATTERNS:
        if pattern.search(path) or pattern.search(decoded):
            findings.append(f"Possible path traversal detected: {pattern.pattern}")
    return findings


def sanitize_html(text: str) -> str:
    """Remove dangerous HTML tags and attributes from *text*.

    This is a lightweight sanitizer — for production HTML rendering
    consider ``bleach`` or ``lxml.html``.
    """
    if not text:
        return ""
    # Strip script/style blocks
    text = re.sub(r"<\s*script[^>]*>.*?</\s*script\s*>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<\s*style[^>]*>.*?</\s*style\s*>", "", text, flags=re.IGNORECASE | re.DOTALL)
    # Strip event handlers
    text = re.sub(r'\bon\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bon\w+\s*=\s*\S+', '', text, flags=re.IGNORECASE)
    # Strip remaining dangerous tags
    text = re.sub(r"<\s*(script|iframe|object|embed|form|applet|meta|link|base|iframe|video|audio)\b[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</?\s*(script|iframe|object|embed|form|applet)\b[^>]*>", "", text, flags=re.IGNORECASE)
    # Unescape angle brackets
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    return text


def validate_input(
    value: str,
    *,
    max_length: int = 10_000,
    check_sql: bool = True,
    check_xss: bool = True,
    check_traversal: bool = False,
) -> list[str]:
    """Comprehensive input validation.

    Returns a list of findings (empty list means the input is clean).
    """
    findings: list[str] = []

    if not value:
        return findings

    if len(value) > max_length:
        findings.append(f"Input exceeds maximum length of {max_length} characters.")

    if check_sql:
        findings.extend(check_sql_injection(value))

    if check_xss:
        findings.extend(check_xss(value))

    if check_traversal:
        findings.extend(check_path_traversal(value))

    return findings


def is_safe_path(path: str) -> bool:
    """Return ``True`` if *path* does not contain traversal sequences."""
    decoded = urllib.parse.unquote(urllib.parse.unquote(path))
    if ".." in decoded:
        return False
    if "\\" in decoded:
        return False
    if any(c in path for c in ("\0", "%00")):
        return False
    return True
