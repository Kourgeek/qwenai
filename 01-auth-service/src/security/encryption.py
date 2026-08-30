"""Encryption utilities for HyperScale Marketplace.

Provides AES-256-GCM encryption/decryption, key management helpers,
and cryptographically secure token generation.
"""

from __future__ import annotations

import os
import secrets
import base64
import logging
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

_AES_KEY_SIZE: int = 32          # 256-bit AES
_SALT_SIZE: int = 16
_IV_SIZE: int = 12               # 96-bit IV for GCM (recommended)
_PBKDF2_ITERATIONS: int = 480_000  # OWASP 2023 recommendation for SHA-256


# ------------------------------------------------------------------
# Key derivation
# ------------------------------------------------------------------

def derive_key(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """Derive a 256-bit AES key from a password using PBKDF2-HMAC-SHA256.

    Returns ``(key, salt)``.
    """
    if salt is None:
        salt = os.urandom(_SALT_SIZE)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=_AES_KEY_SIZE,
        salt=salt,
        iterations=_PBKDF2_ITERATIONS,
        backend=default_backend(),
    )
    key = kdf.derive(password.encode("utf-8"))
    return key, salt


def generate_random_key() -> bytes:
    """Generate a cryptographically random 256-bit key."""
    return os.urandom(_AES_KEY_SIZE)


# ------------------------------------------------------------------
# Encryption / Decryption
# ------------------------------------------------------------------

def encrypt_aes_gcm(plaintext: str, key: bytes) -> str:
    """Encrypt *plaintext* with AES-256-GCM.

    Returns a base64-encoded string containing ``iv:ciphertext:tag``.
    """
    if len(key) != _AES_KEY_SIZE:
        raise ValueError(f"Key must be {_AES_KEY_SIZE} bytes, got {len(key)}")

    iv = os.urandom(_IV_SIZE)
    aesgcm = AESGCM(key)
    nonce_and_ct = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)
    # AESGCM.encrypt returns ciphertext || tag
    ct = nonce_and_ct[:-16]
    tag = nonce_and_ct[-16:]
    encoded = base64.b64encode(iv + ct + tag).decode("ascii")
    return encoded


def decrypt_aes_gcm(encrypted_b64: str, key: bytes) -> str:
    """Decrypt an AES-256-GCM encrypted string produced by :func:`encrypt_aes_gcm`.

    Returns the original plaintext.
    """
    if len(key) != _AES_KEY_SIZE:
        raise ValueError(f"Key must be {_AES_KEY_SIZE} bytes, got {len(key)}")

    raw = base64.b64decode(encrypted_b64)
    if len(raw) < _IV_SIZE + 16:  # IV + minimum tag
        raise ValueError("Encrypted data is too short.")

    iv = raw[:_IV_SIZE]
    ct_tag = raw[_IV_SIZE:]
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(iv, ct_tag, None)
        return plaintext.decode("utf-8")
    except Exception as exc:
        logger.warning("AES-GCM decryption failed: %s", exc)
        raise ValueError("Decryption failed — invalid key or corrupted data") from exc


# ------------------------------------------------------------------
# Token generation
# ------------------------------------------------------------------

def generate_secure_token(bytes_length: int = 32) -> str:
    """Generate a URL-safe, cryptographically secure token.

    Uses ``secrets.token_urlsafe`` which is suitable for password reset
    tokens, CSRF tokens, and similar use-cases.
    """
    return secrets.token_urlsafe(bytes_length)


def generate_api_key(prefix: str = "hsm", bytes_length: int = 32) -> str:
    """Generate a human-readable API key with an optional prefix.

    Format: ``<prefix>_<random>``
    """
    random_part = secrets.token_hex(bytes_length)
    return f"{prefix}_{random_part}"


def generate_refresh_token() -> str:
    """Generate a refresh token (64 bytes of randomness, URL-safe)."""
    return secrets.token_urlsafe(64)


# ------------------------------------------------------------------
# Key management helpers
# ------------------------------------------------------------------

class KeyStore:
    """In-memory key store for development / testing.

    In production, replace with HashiCorp Vault, AWS KMS, or similar.
    """

    def __init__(self) -> None:
        self._keys: dict[str, bytes] = {}

    def store(self, key_id: str, key: bytes) -> None:
        """Store a key by *key_id*."""
        if len(key) != _AES_KEY_SIZE:
            raise ValueError(f"Key must be {_AES_KEY_SIZE} bytes.")
        self._keys[key_id] = key

    def get(self, key_id: str) -> Optional[bytes]:
        """Retrieve a key by *key_id*."""
        return self._keys.get(key_id)

    def delete(self, key_id: str) -> None:
        """Remove a key by *key_id*."""
        self._keys.pop(key_id, None)

    def rotate(self, key_id: str, new_key: bytes) -> None:
        """Atomically replace *key_id* with *new_key*."""
        if len(new_key) != _AES_KEY_SIZE:
            raise ValueError(f"Key must be {_AES_KEY_SIZE} bytes.")
        self._keys[key_id] = new_key

    def list_keys(self) -> list[str]:
        """Return all stored key IDs."""
        return list(self._keys.keys())


# Module-level default key store
_default_store = KeyStore()


def get_default_store() -> KeyStore:
    """Return the module-level default key store."""
    return _default_store
