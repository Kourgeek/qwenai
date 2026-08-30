"""Security module for HyperScale Marketplace.

Exports public utilities for password policy, rate limiting,
input validation, encryption, security headers, and audit logging.
"""

from .password_policy import (
    PasswordValidationError,
    validate_password,
    check_password_against_history,
    is_common_password,
)
from .rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    InMemoryStore,
    RedisStore,
    RateLimitStore,
    get_client_ip,
)
from .input_validation import (
    ValidationError,
    validate_email,
    validate_phone,
    validate_url,
    check_sql_injection,
    check_xss,
    check_path_traversal,
    sanitize_html,
    validate_input,
    is_safe_path,
)
from .encryption import (
    derive_key,
    generate_random_key,
    encrypt_aes_gcm,
    decrypt_aes_gcm,
    generate_secure_token,
    generate_api_key,
    generate_refresh_token,
    KeyStore,
    get_default_store,
)
from .headers import (
    SecurityHeadersMiddleware,
    add_security_headers,
    DEFAULT_HEADERS,
    development_headers,
    production_headers,
    staging_headers,
)

__all__ = [
    # Password policy
    "validate_password",
    "check_password_against_history",
    "is_common_password",
    "PasswordValidationError",
    # Rate limiting
    "RateLimiter",
    "RateLimitConfig",
    "InMemoryStore",
    "RedisStore",
    "RateLimitStore",
    "get_client_ip",
    # Input validation
    "validate_email",
    "validate_phone",
    "validate_url",
    "check_sql_injection",
    "check_xss",
    "check_path_traversal",
    "sanitize_html",
    "validate_input",
    "is_safe_path",
    "ValidationError",
    # Encryption
    "derive_key",
    "generate_random_key",
    "encrypt_aes_gcm",
    "decrypt_aes_gcm",
    "generate_secure_token",
    "generate_api_key",
    "generate_refresh_token",
    "KeyStore",
    "get_default_store",
    # Security headers
    "SecurityHeadersMiddleware",
    "add_security_headers",
    "DEFAULT_HEADERS",
    "development_headers",
    "production_headers",
    "staging_headers",
]
