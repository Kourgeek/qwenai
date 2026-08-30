"""Helper to add Swagger / ReDoc / OpenAPI spec to a FastAPI application.

Usage in any service::

    from src.main import app
    from common_docs.app_docs import add_docs

    add_docs(
        app,
        title="My Service",
        description="Description of my service",
        version="1.0.0",
    )
"""

from __future__ import annotations

from fastapi import FastAPI


def add_docs(
    app: FastAPI,
    title: str,
    description: str,
    version: str = "1.0.0",
    contact_name: str = "HyperScale Marketplace Team",
    contact_email: str = "team@hyperscale.marketplace",
    terms_of_service_url: str | None = None,
    license_info: dict[str, str] | None = None,
) -> None:
    """Configure Swagger UI, ReDoc, and the OpenAPI JSON endpoint on *app*.

    Parameters
    ----------
    app:
        The FastAPI application to configure.
    title:
        Service name displayed in the docs UI.
    description:
        Multi-line description shown in the docs UI.
    version:
        API version (default ``"1.0.0"``, matches ``FastAPI(version=...)``).
    contact_name:
        Name displayed in the ``/docs`` footer (``"HyperScale Marketplace Team"``).
    contact_email:
        Contact e-mail displayed in the ``/docs`` footer.
    terms_of_service_url:
        Optional URL to a terms-of-service page.
    license_info:
        Optional dict ``{"name": "MIT", "identifier": "MIT"}``.
    """

    # ── FastAPI metadata ──────────────────────────────────────────────
    app.title = title
    app.description = description
    app.version = version

    # ── Swagger / ReDoc / OpenAPI URLs ────────────────────────────────
    app.docs_url = "/docs"
    app.redoc_url = "/redoc"
    app.openapi_url = "/openapi.json"

    # ── Contact / license metadata (rendered in Swagger UI) ───────────
    app.contact_info = {
        "name": contact_name,
        "email": contact_email,
    }

    if terms_of_service_url:
        app.docs_ui_params = {"termsOfService": terms_of_service_url}

    if license_info:
        app.license_info = license_info
