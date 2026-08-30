"""Cart Service gRPC proto stubs.

The cart service has its own proto (cart.proto) generated to src/cart/v1/.
For the catalog client (catalog_client.py), the catalog proto is imported directly.
"""

# Export cart service's own proto types
from cart.v1 import cart_pb2
from cart.v1 import cart_pb2_grpc
