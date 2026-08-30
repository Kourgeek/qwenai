"""Async gRPC client for the Auth service.

Connects to the auth-service at AUTH_SERVICE_HOST:AUTH_SERVICE_PORT
and calls the ``Auth.VerifyToken`` / ``Auth.GetUser`` RPCs.
"""

import grpc

from src.config import settings

# ── stubs (generated at build time by grpcio-tools) ───────────
# The .proto file is expected at:
#   migration_plan/02-user-service/protos/auth_service.proto
# After generation:
#   src/grpc_client/auth_pb2.py
#   src/grpc_client/auth_pb2_grpc.py
#
# For local development these are created on-the-fly below.
# In production the CI pipeline generates them before deploy.

import os
import sys

_PROTO_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "protos")
_GENERATED_DIR = os.path.join(os.path.dirname(__file__))

# Ensure the proto directory is on sys.path so we can import the
# generated modules.
if _PROTO_DIR not in sys.path:
    sys.path.insert(0, _PROTO_DIR)

# Try importing generated modules; they will exist after ``make proto``
# or the Docker build step.
try:
    import auth_pb2
    import auth_pb2_grpc
except ImportError:
    # ── Minimal inline definitions for environments without
    #    pre-generated stubs (e.g. tests / local dev). ──────────
    class _AuthStub:
        def VerifyToken(self, request, timeout=None, metadata=None, wait_for_ready=None, credentials=None):
            return self._channel.unary_unary(
                "/auth.Auth/VerifyToken",
                request_serializer=None,
                response_deserializer=None,
            )(request, timeout, metadata, wait_for_ready, credentials)

        def GetUser(self, request, timeout=None, metadata=None, wait_for_ready=None, credentials=None):
            return self._channel.unary_unary(
                "/auth.Auth/GetUser",
                request_serializer=None,
                response_deserializer=None,
            )(request, timeout, metadata, wait_for_ready, credentials)

    class auth_pb2:
        class VerifyTokenRequest:
            def __init__(self, token: str = ""):
                self.token = token
        class VerifyTokenResponse:
            def __init__(self, *, valid: bool = False, user_id: str = "", email: str = ""):
                self.valid = valid
                self.user_id = user_id
                self.email = email
        class GetUserRequest:
            def __init__(self, token: str = ""):
                self.token = token
        class GetUserResponse:
            def __init__(self, *, user_id: str = "", email: str = "", username: str = ""):
                self.user_id = user_id
                self.email = email
                self.username = username

    class auth_pb2_grpc:
        class AuthStub:
            def __init__(self, channel):
                self._channel = channel
            def VerifyToken(self, request, timeout=None, metadata=None, wait_for_ready=None, credentials=None):
                return self._channel.unary_unary(
                    "/auth.Auth/VerifyToken",
                    request_serializer=lambda r: r,
                    response_deserializer=lambda b: b,
                )(request, timeout, metadata, wait_for_ready, credentials)
            def GetUser(self, request, timeout=None, metadata=None, wait_for_ready=None, credentials=None):
                return self._channel.unary_unary(
                    "/auth.Auth/GetUser",
                    request_serializer=lambda r: r,
                    response_deserializer=lambda b: b,
                )(request, timeout, metadata, wait_for_ready, credentials)

        class AuthServicer:
            pass

        @staticmethod
        def add_AuthServicer_to_server(servicer, server):
            pass


def _get_channel() -> grpc.aio.Channel:
    """Return a secure or insecure gRPC channel to auth-service."""
    target = f"{settings.auth_service_host}:{settings.auth_service_port}"
    channel = grpc.aio.insecure_channel(target)
    return channel


async def verify_token(token: str) -> tuple[bool, str]:
    """Call ``Auth.VerifyToken`` and return ``(valid, detail)``.

    *valid* is ``True`` when the token is syntactically valid and
    not expired.  *detail* holds an error message on failure.
    """
    channel = _get_channel()
    try:
        async with channel:
            stub = auth_pb2_grpc.AuthStub(channel)
            response = await stub.VerifyToken(
                auth_pb2.VerifyTokenRequest(token=token),
                timeout=5.0,
            )
            # The response is a protobuf message; inspect its fields.
            valid = getattr(response, "valid", False)
            return valid, "token verified" if valid else "invalid token"
    except grpc.aio.AioRpcError as exc:
        return False, f"gRPC error: {exc.details()}"
    except Exception as exc:
        return False, f"unexpected error: {exc}"


async def get_user_from_token(token: str) -> dict | None:
    """Call ``Auth.GetUser`` and return user info as a dict.

    Returns ``None`` when the token is invalid.
    """
    channel = _get_channel()
    try:
        async with channel:
            stub = auth_pb2_grpc.AuthStub(channel)
            response = await stub.GetUser(
                auth_pb2.GetUserRequest(token=token),
                timeout=5.0,
            )
            user_id = getattr(response, "user_id", "")
            email = getattr(response, "email", "")
            username = getattr(response, "username", "")
            if not user_id:
                return None
            return {"user_id": user_id, "email": email, "username": username}
    except grpc.aio.AioRpcError as exc:
        return None
    except Exception:
        return None
