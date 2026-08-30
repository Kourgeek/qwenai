"""JWT validation middleware for the Gateway.

Provides request-level authentication by validating JWT tokens
from the Authorization header against the Auth service via gRPC.
"""

import logging
from typing import Optional

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.grpc_client.auth_client import AuthGrpcClient

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


class AuthMiddleware:
    """Validates JWT tokens via gRPC Auth service on each request."""

    def __init__(self, auth_client: AuthGrpcClient):
        self.auth_client = auth_client

    async def __call__(self, request: Request, credentials: Optional[HTTPAuthorizationCredentials] = None):
        """Validate the token and attach user info to request state.

        Args:
            request: FastAPI request object.
            credentials: Bearer token from Authorization header.

        Raises:
            HTTPException: 401 if token is missing/invalid.
        """
        # Skip auth for health, docs, and public auth routes
        path = request.url.path.rstrip("/")
        if path in ("/health", "/docs", "/redoc", "/openapi.json",
                     "/auth/login", "/auth/register", "/auth/forgot-password"):
            return None

        # Extract token
        if credentials is None:
            raise HTTPException(status_code=401, detail="Missing authorization token")

        token = credentials.credentials
        if not token:
            raise HTTPException(status_code=401, detail="Empty authorization token")

        # Validate via gRPC
        try:
            user_info = await self.auth_client.verify_token(token)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        except Exception:
            raise HTTPException(status_code=503, detail="Auth service unavailable")

        # Attach to request state for downstream use
        request.state.user = user_info
        return None


def get_auth_middleware(auth_client: AuthGrpcClient):
    """Factory to create AuthMiddleware instances."""
    return AuthMiddleware(auth_client)
