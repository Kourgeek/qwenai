"""FastAPI application entry-point with gRPC lifecycle management and security hardening."""

from __future__ import annotations

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from grpc import aio
from pydantic import BaseModel, EmailStr

from src.config import get_settings
from src.database import init_db
from src.grpc_server import server as grpc_server_module
from src.middleware.security_headers import AuthSecurityHeadersMiddleware
from src.middleware.request_id import RequestIDMiddleware
from src.repositories.auth_repository import AuthRepository
from src.services.auth_service import (
    AuthService,
    AuthServiceError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
    UserAlreadyExistsError,
    WeakPasswordError,
)
from src.database import async_session_factory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

# ── gRPC server handle (managed by lifespan) ─────────────────────────
_grpc_server: aio.Server | None = None


# ── Pydantic models for HTTP requests ─────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    first_name: str | None = None
    last_name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


# ── Lifespan ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown hooks for the gRPC server."""
    await init_db()
    global _grpc_server
    _grpc_server = aio.server()
    try:
        from src.grpc_server import auth_pb2_grpc
    except ImportError:
        logger.warning(
            "auth_pb2_grpc not found — gRPC will not serve RPCs."
        )
    else:
        auth_pb2_grpc.add_AuthServiceServicer_to_server(
            grpc_server_module.AuthServicer(), _grpc_server
        )
        _grpc_server.add_insecure_port(f"0.0.0.0:{settings.grpc_port}")
        await _grpc_server.start()
        logger.info("gRPC server started on port %d", settings.grpc_port)

    yield

    if _grpc_server:
        await _grpc_server.stop(grace=5)
        logger.info("gRPC server stopped")


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(AuthSecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)


# ── Health ────────────────────────────────────────────────────────────

@app.get("/health", tags=["health"])
async def health() -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": "2.0.0",
    }


# ── Auth HTTP endpoints ───────────────────────────────────────────────

@app.post("/auth/register", tags=["auth"])
async def register(req: RegisterRequest):
    session = async_session_factory()
    try:
        repo = AuthRepository(session)
        service = AuthService(repo)
        result = await service.register(
            email=req.email,
            password=req.password,
            first_name=req.first_name,
            last_name=req.last_name,
        )
        await session.commit()
        return {
            "user_id": result["user_id"],
            "email": result["email"],
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
        }
    except UserAlreadyExistsError as exc:
        await session.rollback()
        return JSONResponse(status_code=409, content={"detail": str(exc)})
    except WeakPasswordError as exc:
        await session.rollback()
        return JSONResponse(status_code=422, content={"detail": str(exc), "errors": exc.errors})
    except AuthServiceError as exc:
        await session.rollback()
        return JSONResponse(status_code=400, content={"detail": str(exc)})
    except Exception as exc:
        await session.rollback()
        logger.exception("Register failed")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
    finally:
        await session.close()


@app.post("/auth/login", tags=["auth"])
async def login(req: LoginRequest):
    session = async_session_factory()
    try:
        repo = AuthRepository(session)
        service = AuthService(repo)
        result = await service.login(email=req.email, password=req.password)
        await session.commit()
        return {
            "user_id": result["user_id"],
            "email": result["email"],
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
        }
    except InvalidCredentialsError as exc:
        await session.rollback()
        return JSONResponse(status_code=401, content={"detail": str(exc)})
    except AuthServiceError as exc:
        await session.rollback()
        return JSONResponse(status_code=400, content={"detail": str(exc)})
    except Exception as exc:
        await session.rollback()
        logger.exception("Login failed")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
    finally:
        await session.close()


@app.post("/auth/refresh", tags=["auth"])
async def refresh(req: RefreshRequest):
    session = async_session_factory()
    try:
        repo = AuthRepository(session)
        service = AuthService(repo)
        result = await service.refresh(refresh_token_value=req.refresh_token)
        await session.commit()
        return {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
        }
    except InvalidTokenError as exc:
        await session.rollback()
        return JSONResponse(status_code=401, content={"detail": str(exc)})
    except TokenExpiredError as exc:
        await session.rollback()
        return JSONResponse(status_code=401, content={"detail": str(exc)})
    except AuthServiceError as exc:
        await session.rollback()
        return JSONResponse(status_code=400, content={"detail": str(exc)})
    except Exception as exc:
        await session.rollback()
        logger.exception("Refresh failed")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
    finally:
        await session.close()


@app.post("/auth/logout", tags=["auth"])
async def logout(req: LogoutRequest):
    session = async_session_factory()
    try:
        repo = AuthRepository(session)
        service = AuthService(repo)
        await service.logout(refresh_token_value=req.refresh_token)
        await session.commit()
        return {"success": True}
    except AuthServiceError as exc:
        await session.rollback()
        return JSONResponse(status_code=400, content={"detail": str(exc)})
    except Exception as exc:
        await session.rollback()
        logger.exception("Logout failed")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
    finally:
        await session.close()


# ── Entry-point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.http_port,
        reload=True,
    )
