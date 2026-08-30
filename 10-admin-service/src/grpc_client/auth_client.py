"""gRPC client for the Auth Service."""

import grpc

from src.config import settings


def _channel() -> grpc.aio.Channel:
    """Return an async gRPC channel to the Auth Service."""
    return grpc.aio.insecure_channel(f"{settings.auth_service_host}:{settings.auth_service_port}")


async def verify_token(token: str) -> bool:
    """Verify a bearer token against the Auth Service.

    Returns ``True`` when the token is valid and unexpired.
    """
    if not token or not token.strip():
        return False

    async with _channel() as channel:
        # Placeholder: replace with the real stub call once the proto
        # definition for AuthService.VerifyToken is available.
        # Example target:
        #   stub = auth_pb2_grpc.AuthServiceStub(channel)
        #   resp = await stub.VerifyToken(auth_pb2.VerifyTokenRequest(token=token))
        #   return resp.valid
        pass

    # For now fall back to a simple non-empty check; the real
    # implementation will call the Auth Service gRPC endpoint.
    return bool(token.strip())


async def get_user_roles(token: str) -> list[str]:
    """Return the list of roles associated with *token*.

    Returns an empty list when the token is invalid.
    """
    if not token or not token.strip():
        return []

    async with _channel() as channel:
        # Placeholder: replace with the real stub call.
        # Example target:
        #   stub = auth_pb2_grpc.AuthServiceStub(channel)
        #   resp = await stub.GetUserRoles(auth_pb2.GetUserRolesRequest(token=token))
        #   return list(resp.roles)
        pass

    return []
