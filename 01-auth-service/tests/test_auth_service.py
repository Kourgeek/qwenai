"""Integration tests for AuthService: register, login, refresh, logout."""

from __future__ import annotations

import uuid

import pytest

from src.services.auth_service import (
    AuthService,
    AuthServiceError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserAlreadyExistsError,
)


@pytest.mark.asyncio
async def test_register_success(auth_service: AuthService) -> None:
    result = await auth_service.register(
        email="new@example.com",
        password="SecurePass123!",
        first_name="Alice",
        last_name="Smith",
    )
    assert result["email"] == "new@example.com"
    assert result["user_id"]
    assert result["access_token"]
    assert result["refresh_token"]


@pytest.mark.asyncio
async def test_register_duplicate(auth_service: AuthService) -> None:
    await auth_service.register(
        email="dup@example.com",
        password="SecurePass123!",
    )
    with pytest.raises(UserAlreadyExistsError):
        await auth_service.register(
            email="dup@example.com",
            password="AnotherPass456!",
        )


@pytest.mark.asyncio
async def test_login_success(auth_service: AuthService, created_user: uuid.UUID) -> None:
    result = await auth_service.login(
        email="test@example.com",
        password="TestPass123!",
    )
    assert result["email"] == "test@example.com"
    assert result["user_id"] == str(created_user)
    assert result["access_token"]
    assert result["refresh_token"]


@pytest.mark.asyncio
async def test_login_wrong_password(auth_service: AuthService) -> None:
    with pytest.raises(InvalidCredentialsError):
        await auth_service.login(
            email="test@example.com",
            password="WrongPassword!",
        )


@pytest.mark.asyncio
async def test_login_nonexistent_user(auth_service: AuthService) -> None:
    with pytest.raises(InvalidCredentialsError):
        await auth_service.login(
            email="nobody@example.com",
            password="AnyPassword!",
        )


@pytest.mark.asyncio
async def test_refresh_flow(auth_service: AuthService) -> None:
    # Register a user
    reg_result = await auth_service.register(
        email="refresh@example.com",
        password="SecurePass123!",
    )
    old_refresh = reg_result["refresh_token"]

    # Refresh the access token
    refresh_result = await auth_service.refresh(refresh_token_value=old_refresh)
    assert refresh_result["access_token"]
    assert refresh_result["refresh_token"]
    # The old refresh token should no longer be valid (rotation)
    with pytest.raises(InvalidTokenError):
        await auth_service.refresh(refresh_token_value=old_refresh)


@pytest.mark.asyncio
async def test_logout_revokes_token(auth_service: AuthService) -> None:
    reg_result = await auth_service.register(
        email="logout@example.com",
        password="SecurePass123!",
    )
    refresh_token = reg_result["refresh_token"]

    await auth_service.logout(refresh_token_value=refresh_token)

    # After logout the token should be invalid
    with pytest.raises(InvalidTokenError):
        await auth_service.refresh(refresh_token_value=refresh_token)


@pytest.mark.asyncio
async def test_forgot_password_existing(auth_service: AuthService) -> None:
    # Register first
    await auth_service.register(
        email="forgot@example.com",
        password="SecurePass123!",
    )
    result = await auth_service.forgot_password("forgot@example.com")
    assert result["email"] == "forgot@example.com"
    assert result["reset_token"] == "dummy-reset-token"  # Phase-2 stub


@pytest.mark.asyncio
async def test_forgot_password_nonexistent(auth_service: AuthService) -> None:
    result = await auth_service.forgot_password("nobody@example.com")
    assert result["email"] == "nobody@example.com"
    assert result["reset_token"] == "dummy-reset-token"  # stub — no leak
