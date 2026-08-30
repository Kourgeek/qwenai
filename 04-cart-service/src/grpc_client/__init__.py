"""Cart Service gRPC proto stubs.

The cart service has its own proto (cart.proto) generated to src/cart/v1/.
"""

from cart.v1 import cart_pb2
from cart.v1 import cart_pb2_grpc

# Alias missing response message types that the service code expects
# but the proto defines with different names (Cart->CartResponse, etc.)
if not hasattr(cart_pb2, 'CartResponse'):
    class _CartResponse:
        def __init__(self, **kwargs):
            self.user_id = kwargs.get('user_id', '')
            self.items = kwargs.get('items', [])
            self.total = kwargs.get('total', 0.0)
    cart_pb2.CartResponse = _CartResponse

if not hasattr(cart_pb2, 'CartItemResponse'):
    class _CartItemResponse:
        def __init__(self, **kwargs):
            self.user_id = kwargs.get('user_id', '')
            self.items = kwargs.get('items', [])
            self.total = kwargs.get('total', 0.0)
    cart_pb2.CartItemResponse = _CartItemResponse

if not hasattr(cart_pb2, 'EmptyResponse'):
    class _EmptyResponse:
        def __init__(self, **kwargs):
            pass
    cart_pb2.EmptyResponse = _EmptyResponse
