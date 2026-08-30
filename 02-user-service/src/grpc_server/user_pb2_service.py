"""gRPC service implementation for the User service.

Implements the RPCs defined in ``protos/user_service.proto``:
    GetUser, UpdateUser, AddAddress, UpdateAddress, DeleteAddress,
    GetUserAddresses, AddToWishlist, GetUserWishlist, RemoveFromWishlist
"""

import logging
import uuid

import grpc
import grpc.aio

from src.database import async_session_factory
from src.grpc_client.auth_client import get_user_from_token
from src.services.address_service import AddressService
from src.services.user_service import UserService
from src.services.wishlist_service import WishlistService

logger = logging.getLogger(__name__)

# в”Ђв”Ђ Import generated protobuf bindings в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
# In production these are generated at build time.
# For local dev / tests we provide minimal fallback definitions
# (see auth_client.py for the pattern).

try:
    import user_pb2
    import user_pb2_grpc
except ImportError:
    # в”Ђв”Ђ Minimal inline stubs for environments without generated code.
    class _Proto:
        class User:
            def __init__(
                self,
                id: str = "",
                email: str = "",
                username: str = "",
                display_name: str = "",
                phone_number: str = "",
                avatar_url: str = "",
                is_active: bool = False,
            ):
                self.id = id
                self.email = email
                self.username = username
                self.display_name = display_name
                self.phone_number = phone_number
                self.avatar_url = avatar_url
                self.is_active = is_active

        class Address:
            def __init__(
                self,
                id: str = "",
                user_id: str = "",
                street: str = "",
                city: str = "",
                state: str = "",
                postal_code: str = "",
                country: str = "",
                is_default: bool = False,
                address_type: str = "",
            ):
                self.id = id
                self.user_id = user_id
                self.street = street
                self.city = city
                self.state = state
                self.postal_code = postal_code
                self.country = country
                self.is_default = is_default
                self.address_type = address_type

        class WishlistItem:
            def __init__(
                self,
                id: str = "",
                user_id: str = "",
                product_id: str = "",
                added_at: str = "",
            ):
                self.id = id
                self.user_id = user_id
                self.product_id = product_id
                self.added_at = added_at

        class GetUserRequest:
            def __init__(self, user_id: str = ""):
                self.user_id = user_id

        class UpdateUserRequest:
            def __init__(
                self,
                user_id: str = "",
                email: str = "",
                username: str = "",
                display_name: str = "",
                phone_number: str = "",
                avatar_url: str = "",
                is_active: bool = False,
            ):
                self.user_id = user_id
                self.email = email
                self.username = username
                self.display_name = display_name
                self.phone_number = phone_number
                self.avatar_url = avatar_url
                self.is_active = is_active

        class AddAddressRequest:
            def __init__(
                self,
                user_id: str = "",
                street: str = "",
                city: str = "",
                postal_code: str = "",
                country: str = "",
                state: str = "",
                is_default: bool = False,
                address_type: str = "",
            ):
                self.user_id = user_id
                self.street = street
                self.city = city
                self.postal_code = postal_code
                self.country = country
                self.state = state
                self.is_default = is_default
                self.address_type = address_type

        class UpdateAddressRequest:
            def __init__(
                self,
                address_id: str = "",
                street: str = "",
                city: str = "",
                state: str = "",
                postal_code: str = "",
                country: str = "",
                is_default: bool = False,
            ):
                self.address_id = address_id
                self.street = street
                self.city = city
                self.state = state
                self.postal_code = postal_code
                self.country = country
                self.is_default = is_default

        class DeleteAddressRequest:
            def __init__(self, address_id: str = ""):
                self.address_id = address_id

        class GetUserAddressesRequest:
            def __init__(self, user_id: str = ""):
                self.user_id = user_id

        class AddToWishlistRequest:
            def __init__(self, user_id: str = "", product_id: str = ""):
                self.user_id = user_id
                self.product_id = product_id

        class GetUserWishlistRequest:
            def __init__(self, user_id: str = ""):
                self.user_id = user_id

        class RemoveFromWishlistRequest:
            def __init__(self, user_id: str = "", product_id: str = ""):
                self.user_id = user_id
                self.product_id = product_id

    user_pb2 = _Proto
    user_pb2_grpc = type("Module", (), {
        "UserServiceServicer": object,
        "add_UserServiceServicer_to_server": lambda self, servicer, server, **kwargs: None,
    })()


def _uuid_or_none(value: str) -> uuid.UUID | None:
    """Parse a UUID string or return ``None``."""
    if not value:
        return None
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        return None


class UserServiceServicer(user_pb2_grpc.UserServiceServicer):
    """gRPC implementation of the User service."""

    async def GetUser(self, request, context):
        user_id = _uuid_or_none(request.user_id)
        if user_id is None:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "user_id is required")
            return user_pb2.User()

        async with async_session_factory() as session:
            service = UserService(session)
            dto = await service.get_user(user_id)

        if dto is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"User {user_id} not found")
            return user_pb2.User()

        return user_pb2.User(
            id=str(dto.id),
            email=dto.email,
            username=dto.username,
            display_name=dto.display_name or "",
            phone_number=dto.phone_number or "",
            avatar_url=dto.avatar_url or "",
            is_active=dto.is_active,
        )

    async def UpdateUser(self, request, context):
        user_id = _uuid_or_none(request.user_id)
        if user_id is None:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "user_id is required")
            return user_pb2.User()

        async with async_session_factory() as session:
            service = UserService(session)
            try:
                dto = await service.update_user(
                    user_id,
                    email=request.email or None,
                    username=request.username or None,
                    display_name=request.display_name or None,
                    phone_number=request.phone_number or None,
                    avatar_url=request.avatar_url or None,
                    is_active=request.is_active,
                )
            except ValueError as exc:
                context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
                return user_pb2.User()

        return user_pb2.User(
            id=str(dto.id),
            email=dto.email,
            username=dto.username,
            display_name=dto.display_name or "",
            phone_number=dto.phone_number or "",
            avatar_url=dto.avatar_url or "",
            is_active=dto.is_active,
        )

    async def AddAddress(self, request, context):
        user_id = _uuid_or_none(request.user_id)
        if user_id is None:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "user_id is required")
            return user_pb2.Address()

        async with async_session_factory() as session:
            service = AddressService(session)
            address = await service.add_address(
                user_id,
                street=request.street,
                city=request.city,
                postal_code=request.postal_code,
                country=request.country or "RU",
                state=request.state or None,
                is_default=request.is_default,
                address_type=request.address_type or "shipping",
            )

        return user_pb2.Address(
            id=str(address.id),
            user_id=str(address.user_id),
            street=address.street,
            city=address.city,
            state=address.state or "",
            postal_code=address.postal_code,
            country=address.country,
            is_default=address.is_default,
            address_type=address.address_type,
        )

    async def UpdateAddress(self, request, context):
        address_id = _uuid_or_none(request.address_id)
        if address_id is None:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "address_id is required")
            return user_pb2.Address()

        try:
            async with async_session_factory() as session:
                service = AddressService(session)
                address = await service.update_address(
                    address_id,
                    street=request.street or None,
                    city=request.city or None,
                    state=request.state or None,
                    postal_code=request.postal_code or None,
                    country=request.country or None,
                    is_default=request.is_default,
                )
        except ValueError as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
            return user_pb2.Address()

        return user_pb2.Address(
            id=str(address.id),
            user_id=str(address.user_id),
            street=address.street,
            city=address.city,
            state=address.state or "",
            postal_code=address.postal_code,
            country=address.country,
            is_default=address.is_default,
            address_type=address.address_type,
        )

    async def DeleteAddress(self, request, context):
        address_id = _uuid_or_none(request.address_id)
        if address_id is None:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "address_id is required")
            return user_pb2.DeleteAddressResponse()

        try:
            async with async_session_factory() as session:
                service = AddressService(session)
                await service.delete_address(address_id)
        except ValueError as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))

        return user_pb2.DeleteAddressResponse(success=True)

    async def GetUserAddresses(self, request, context):
        user_id = _uuid_or_none(request.user_id)
        if user_id is None:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "user_id is required")
            return user_pb2.AddressList()

        async with async_session_factory() as session:
            service = AddressService(session)
            addresses = await service.list_addresses(user_id)

        return user_pb2.AddressList(
            addresses=[
                user_pb2.Address(
                    id=str(a.id),
                    user_id=str(a.user_id),
                    street=a.street,
                    city=a.city,
                    state=a.state or "",
                    postal_code=a.postal_code,
                    country=a.country,
                    is_default=a.is_default,
                    address_type=a.address_type,
                )
                for a in addresses
            ]
        )

    async def AddToWishlist(self, request, context):
        user_id = _uuid_or_none(request.user_id)
        if user_id is None:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "user_id is required")
            return user_pb2.WishlistItem()

        if not request.product_id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "product_id is required")
            return user_pb2.WishlistItem()

        try:
            async with async_session_factory() as session:
                service = WishlistService(session)
                item = await service.add_to_wishlist(user_id, request.product_id)
        except ValueError as exc:
            context.abort(grpc.StatusCode.ALREADY_EXISTS, str(exc))
            return user_pb2.WishlistItem()

        return user_pb2.WishlistItem(
            id=str(item.id),
            user_id=str(item.user_id),
            product_id=item.product_id,
            added_at=str(item.added_at),
        )

    async def GetUserWishlist(self, request, context):
        user_id = _uuid_or_none(request.user_id)
        if user_id is None:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "user_id is required")
            return user_pb2.WishlistItemList()

        async with async_session_factory() as session:
            service = WishlistService(session)
            items = await service.get_wishlist(user_id)

        return user_pb2.WishlistItemList(
            items=[
                user_pb2.WishlistItem(
                    id=str(i.id),
                    user_id=str(i.user_id),
                    product_id=i.product_id,
                    added_at=str(i.added_at),
                )
                for i in items
            ]
        )

    async def RemoveFromWishlist(self, request, context):
        user_id = _uuid_or_none(request.user_id)
        if user_id is None:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "user_id is required")
            return user_pb2.RemoveFromWishlistResponse()

        if not request.product_id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "product_id is required")
            return user_pb2.RemoveFromWishlistResponse()

        try:
            async with async_session_factory() as session:
                service = WishlistService(session)
                removed = await service.remove_from_wishlist(user_id, request.product_id)
        except ValueError as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))

        return user_pb2.RemoveFromWishlistResponse(removed=removed)


async def serve(grpc_port: int = 50053) -> grpc.aio.Server:
    """Start the gRPC server and return the running server object."""
    server = grpc.aio.server()
    user_pb2_grpc.add_UserServiceServicer_to_server(
        UserServiceServicer(), server
    )
    server.add_insecure_port(f"[::]:{grpc_port}")
    await server.start()
    logger.info("gRPC server listening on port %d", grpc_port)
    return server
