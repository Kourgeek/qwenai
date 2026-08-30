"""gRPC service implementation for CartService.

Generated from cart.proto via grpc_tools.protoc.
"""

from __future__ import annotations

import logging
from typing import Any

import grpc

# ------------------------------------------------------------------
# Proto-generated imports — in production these come from
# ``python -m grpc_tools.protoc``.  We shim the expected symbols here.
# ------------------------------------------------------------------
from src.grpc_client import cart_pb2, cart_pb2_grpc  # type: ignore[attr-defined]  # noqa: E5F1

from src.services.cart_service import cart_service

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Proto message type aliases (shim — matches generated output)
# ------------------------------------------------------------------
GetCartRequest = cart_pb2.GetCartRequest
AddItemRequest = cart_pb2.AddItemRequest
UpdateItemRequest = cart_pb2.UpdateItemRequest
RemoveItemRequest = cart_pb2.RemoveItemRequest
ClearCartRequest = cart_pb2.ClearCartRequest
SaveForLaterRequest = cart_pb2.SaveForLaterRequest
MoveToCartRequest = cart_pb2.MoveToCartRequest

CartItem = cart_pb2.CartItem
CartResponse = cart_pb2.CartResponse
CartItemResponse = cart_pb2.CartItemResponse
EmptyResponse = cart_pb2.EmptyResponse


class CartServiceServicer(cart_pb2_grpc.CartServiceServicer):  # type: ignore[name-defined]
    """gRPC servicer delegating to CartService business logic."""

    async def GetCart(self, request: GetCartRequest, context: grpc.aio.ServicerContext) -> CartResponse:  # type: ignore[override]
        user_id = request.user_id
        if not user_id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("user_id is required")
            return CartResponse()

        cart = await cart_service.get_cart(user_id)
        return _cart_to_response(cart)

    async def AddItem(self, request: AddItemRequest, context: grpc.aio.ServicerContext) -> CartItemResponse:  # type: ignore[override]
        if not request.user_id or not request.product_id or request.quantity <= 0:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("user_id, product_id, and quantity > 0 are required")
            return CartItemResponse()

        cart = await cart_service.add_item(request.user_id, request.product_id, request.quantity)
        return _cart_to_response(cart)

    async def UpdateItem(self, request: UpdateItemRequest, context: grpc.aio.ServicerContext) -> CartItemResponse:  # type: ignore[override]
        if not request.user_id or not request.product_id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("user_id and product_id are required")
            return CartItemResponse()

        cart = await cart_service.update_item(request.user_id, request.product_id, request.quantity)
        return _cart_to_response(cart)

    async def RemoveItem(self, request: RemoveItemRequest, context: grpc.aio.ServicerContext) -> EmptyResponse:  # type: ignore[override]
        if not request.user_id or not request.product_id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("user_id and product_id are required")
            return EmptyResponse()

        await cart_service.remove_item(request.user_id, request.product_id)
        return EmptyResponse()

    async def ClearCart(self, request: ClearCartRequest, context: grpc.aio.ServicerContext) -> EmptyResponse:  # type: ignore[override]
        if not request.user_id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("user_id is required")
            return EmptyResponse()

        await cart_service.clear_cart(request.user_id)
        return EmptyResponse()

    async def SaveForLater(self, request: SaveForLaterRequest, context: grpc.aio.ServicerContext) -> EmptyResponse:  # type: ignore[override]
        if not request.user_id or not request.product_id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("user_id and product_id are required")
            return EmptyResponse()

        await cart_service.save_for_later(request.user_id, request.product_id)
        return EmptyResponse()

    async def MoveToCart(self, request: MoveToCartRequest, context: grpc.aio.ServicerContext) -> EmptyResponse:  # type: ignore[override]
        if not request.user_id or not request.product_id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("user_id and product_id are required")
            return EmptyResponse()

        await cart_service.move_to_cart(request.user_id, request.product_id)
        return EmptyResponse()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _cart_to_response(cart: dict[str, Any]) -> CartResponse:  # type: ignore[name-defined]
    items = [
        CartItem(  # type: ignore[call-arg]
            product_id=i["product_id"],
            product_name=i["product_name"],
            unit_price=i["unit_price"],
            quantity=i["quantity"],
            subtotal=i["unit_price"] * i["quantity"],
        )
        for i in cart.get("items", [])
    ]
    return CartResponse(  # type: ignore[call-arg]
        user_id=cart.get("user_id", ""),
        items=items,
        total=cart.get("total", 0.0),
    )
