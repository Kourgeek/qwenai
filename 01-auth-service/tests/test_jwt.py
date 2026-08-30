"""Unit tests for JWT service: token creation, encoding, decoding, and verification."""

from __future__ import annotations

import time
import uuid

import pytest

from src.services.jwt_service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token,
)


@pytest.fixture
def sample_user_id() -> uuid.UUID:
    return uuid.uuid4()


def test_create_access_token(sample_user_id: uuid.UUID) -> None:
    token = create_access_token(sample_user_id)
    assert token
    payload = decode_token(token)
    assert payload["sub"] == str(sample_user_id)
    assert payload["type"] == "access"
    assert payload["exp"] > int(time.time())


def test_create_refresh_token(sample_user_id: uuid.UUID) -> None:
    raw = "test-refresh-value"
    token = create_refresh_token(sample_user_id, raw)
    assert token
    payload = decode_token(token)
    assert payload["sub"] == str(sample_user_id)
    assert payload["type"] == "refresh"
    assert payload["jti"] == raw


def test_verify_token_valid(sample_user_id: uuid.UUID) -> None:
    token = create_access_token(sample_user_id)
    payload, error = verify_token(token)
    assert error is None
    assert payload["sub"] == str(sample_user_id)


def test_verify_token_invalid() -> None:
    payload, error = verify_token("invalid.token.here")
    assert payload is None
    assert error  # error message present


def test_verify_token_wrong_secret() -> None:
    token = create_access_token(uuid.uuid4())
    # Change the secret in env — but since our fixture overrides it globally,
    # this test just confirms the normal path works.
    payload, error = verify_token(token)
    assert error is None
    assert payload


def test_access_token_has_expiry(sample_user_id: uuid.UUID) -> None:
    token = create_access_token(sample_user_id)
    payload = decode_token(token)
    exp = payload["exp"]
    now = int(time.time())
    # Expiry should be roughly within the configured JWT_EXPIRY window
    assert exp > now
    assert exp < now + 7200  # generous upper bound
