"""gRPC AuthServicer implementing the authentication RPCs."""

from __future__ import annotations

import logging
import uuid

import grpc

# Import the generated_pb2 and generated_pb2_grpc modules.
try:
    from src.auth.v1 import auth_pb2, auth_pb2_grpc
except ImportError:
    auth_pb2 = None
    auth_pb2_grpc = None

from src.config import get_settings
from src.repositories.auth_repository import AuthRepository
from src.services.auth_service import (
    AuthService,
    AuthServiceError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
    UserAlreadyExistsError,
)
from src.database import async_session_factory

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthServicer(auth_pb2_grpc.AuthServiceServicer):
    """gRPC service implementation for authentication."""

    def _make_repo(self):
        """Create an AuthRepository with a new session."""
        session = async_session_factory()
        return AuthRepository(session)

    async def Register(
        self, request: auth_pb2.RegisterRequest, context: grpc.ServicerContext
    ) -> auth_pb2.RegisterResponse:
        session = async_session_factory()
        try:
            repository = AuthRepository(session)
            service = AuthService(repository)
            result = await service.register(
                email=request.email,
                password=request.password,
                first_name=request.first_name or None,
                last_name=request.last_name or None,
            )
            await session.commit()
            return auth_pb2.RegisterResponse(
                user_id=result["user_id"],
                email=result["email"],
                access_token=result["access_token"],
                refresh_token=result["refresh_token"],
            )
        except UserAlreadyExistsError as exc:
            await session.rollback()
            context.abort(grpc.StatusCode.ALREADY_EXISTS, str(exc))
            raise
        except AuthServiceError as exc:
            await session.rollback()
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
            raise
        except Exception as exc:
            await session.rollback()
            logger.exception("Register RPC failed")
            context.abort(grpc.StatusCode.INTERNAL, "Internal server error")
            raise
        finally:
            await session.close()

    async def Login(
        self, request: auth_pb2.LoginRequest, context: grpc.ServicerContext
    ) -> auth_pb2.LoginResponse:
        session = async_session_factory()
        try:
            repository = AuthRepository(session)
            service = AuthService(repository)
            result = await service.login(email=request.email, password=request.password)
            await session.commit()
            return auth_pb2.LoginResponse(
                user_id=result["user_id"],
                email=result["email"],
                access_token=result["access_token"],
                refresh_token=result["refresh_token"],
            )
        except InvalidCredentialsError as exc:
            await session.rollback()
            context.abort(grpc.StatusCode.UNAUTHENTICATED, str(exc))
            raise
        except AuthServiceError as exc:
            await session.rollback()
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
            raise
        except Exception as exc:
            await session.rollback()
            logger.exception("Login RPC failed")
            context.abort(grpc.StatusCode.INTERNAL, "Internal server error")
            raise
        finally:
            await session.close()

    async def Refresh(
        self, request: auth_pb2.RefreshRequest, context: grpc.ServicerContext
    ) -> auth_pb2.RefreshResponse:
        session = async_session_factory()
        try:
            repository = AuthRepository(session)
            service = AuthService(repository)
            result = await service.refresh(refresh_token_value=request.refresh_token)
            await session.commit()
            return auth_pb2.RefreshResponse(
                access_token=result["access_token"],
                refresh_token=result["refresh_token"],
            )
        except InvalidTokenError as exc:
            await session.rollback()
            context.abort(grpc.StatusCode.UNAUTHENTICATED, str(exc))
            raise
        except TokenExpiredError as exc:
            await session.rollback()
            context.abort(grpc.StatusCode.UNAUTHENTICATED, str(exc))
            raise
        except AuthServiceError as exc:
            await session.rollback()
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
            raise
        except Exception as exc:
            await session.rollback()
            logger.exception("Refresh RPC failed")
            context.abort(grpc.StatusCode.INTERNAL, "Internal server error")
            raise
        finally:
            await session.close()

    async def Logout(
        self, request: auth_pb2.LogoutRequest, context: grpc.ServicerContext
    ) -> auth_pb2.LogoutResponse:
        session = async_session_factory()
        try:
            repository = AuthRepository(session)
            service = AuthService(repository)
            await service.logout(refresh_token_value=request.refresh_token)
            await session.commit()
            return auth_pb2.LogoutResponse(success=True)
        except AuthServiceError as exc:
            await session.rollback()
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
            raise
        except Exception as exc:
            await session.rollback()
            logger.exception("Logout RPC failed")
            context.abort(grpc.StatusCode.INTERNAL, "Internal server error")
            raise
        finally:
            await session.close()

    async def ForgotPassword(
        self,
        request: auth_pb2.ForgotPasswordRequest,
        context: grpc.ServicerContext,
    ) -> auth_pb2.ForgotPasswordResponse:
        session = async_session_factory()
        try:
            repository = AuthRepository(session)
            service = AuthService(repository)
            result = await service.forgot_password(email=request.email)
            return auth_pb2.ForgotPasswordResponse(
                email=result["email"],
                reset_token=result["reset_token"],
            )
        except AuthServiceError as exc:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
            raise
        except Exception as exc:
            logger.exception("ForgotPassword RPC failed")
            context.abort(grpc.StatusCode.INTERNAL, "Internal server error")
            raise
        finally:
            await session.close()


def serve(grpc_port: int = settings.grpc_port) -> None:
    """Start the gRPC server on *grpc_port* (blocking)."""
    if auth_pb2_grpc is None:
        raise RuntimeError(
            "gRPC protobuf modules not found. Run: "
            "grpc_tools.protoc -I protos --python_out=. --grpc_python_out=. "
            "--pyi_out=. protos/auth.proto"
        )

    server = grpc.aio.server()
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthServicer(), server)
    server.add_insecure_port(f"[::]:{grpc_port}")
    logger.info("gRPC server listening on port %d", grpc_port)
    server.start()
    server.wait_for_termination()
