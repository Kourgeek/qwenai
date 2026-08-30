"""Common Pydantic schemas used across HyperScale Marketplace services.

These schemas are referenced in API documentation (OpenAPI / Swagger) via
``response_model``, ``request_body``, ``Field(..., example=...)``, etc.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

# ── Type variables for generic wrappers ───────────────────────────────

T = TypeVar("T")

# ── Pagination ─────────────────────────────────────────────────────────


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page (max 100)",
    )


class PaginationMeta(BaseModel):
    """Pagination metadata included in paginated responses."""

    page: int = Field(example=1)
    page_size: int = Field(example=20)
    total_items: int = Field(example=150)
    total_pages: int = Field(example=8)


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response wrapper.

    Example
    -------
    .. code-block:: json

        {
          "data": [...],
          "meta": {"page": 1, "page_size": 20, "total_items": 150, "total_pages": 8}
        }
    """

    data: list[T]
    meta: PaginationMeta

    model_config = {"json_schema_extra": {"example": {"data": [], "meta": {"page": 1, "page_size": 20, "total_items": 0, "total_pages": 0}}}}


# ── Error response ─────────────────────────────────────────────────────


class ErrorDetail(BaseModel):
    """A single validation / business error detail."""

    field: str | None = Field(default=None, example="email")
    message: str = Field(example="must be a valid email address")
    code: str = Field(default="VALIDATION_ERROR", example="VALIDATION_ERROR")


class ErrorResponse(BaseModel):
    """Standard error response envelope.

    Example
    -------
    .. code-block:: json

        {
          "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": [
              {"field": "email", "message": "must be a valid email address", "code": "INVALID_EMAIL"}
            ]
          }
        }
    """

    error: dict[str, Any] = Field(
        example={
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": [
                {"field": "email", "message": "must be a valid email address", "code": "INVALID_EMAIL"}
            ],
        }
    )


# ── Success response wrapper ───────────────────────────────────────────


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response envelope for single-resource endpoints.

    Example
    -------
    .. code-block:: json

        {
          "success": true,
          "data": {"id": "abc123", "name": "Widget"},
          "message": "Resource created successfully"
        }
    """

    success: bool = Field(default=True, example=True)
    data: T | None = Field(default=None, example={"id": "abc123", "name": "Widget"})
    message: str = Field(default="Operation completed successfully", example="Operation completed successfully")


class MessageResponse(BaseModel):
    """Minimal success response for endpoints that return no payload.

    Example
    -------
    .. code-block:: json

        {
          "success": true,
          "message": "Resource deleted successfully"
        }
    """

    success: bool = Field(default=True, example=True)
    message: str = Field(example="Operation completed successfully")


# ── Health check schemas ───────────────────────────────────────────────


class DependencyStatus(BaseModel):
    """Status of a single downstream dependency."""

    name: str = Field(example="postgresql")
    status: str = Field(example="healthy")
    response_time_ms: float | None = Field(default=None, example=2.5)
    detail: dict[str, Any] | None = Field(default=None, example={"version": "16.1"})


class HealthCheckResponse(BaseModel):
    """Response for ``/health`` (detailed health).

    Example
    -------
    .. code-block:: json

        {
          "status": "healthy",
          "service": "auth-service",
          "version": "2.0.0",
          "dependencies": [
            {"name": "postgresql", "status": "healthy", "response_time_ms": 2.5}
          ],
          "timestamp": "2026-01-15T10:30:00Z"
        }
    """

    status: str = Field(example="healthy")
    service: str = Field(example="auth-service")
    version: str = Field(example="2.0.0")
    dependencies: list[DependencyStatus] = Field(default_factory=list)
    timestamp: str = Field(example="2026-01-15T10:30:00Z")


class ReadinessResponse(BaseModel):
    """Response for ``/health/ready`` (readiness probe).

    Example
    -------
    .. code-block:: json

        {
          "status": "ready",
          "checks": {
            "database": "healthy",
            "redis": "healthy"
          },
          "timestamp": "2026-01-15T10:30:00Z"
        }
    """

    status: str = Field(example="ready")
    checks: dict[str, str] = Field(example={"database": "healthy", "redis": "healthy"})
    timestamp: str = Field(example="2026-01-15T10:30:00Z")
