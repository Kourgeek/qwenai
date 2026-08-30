# Order Service API Documentation

Order management service handling order creation, status tracking, cancellation, and order history.

---

## Table of Contents

- [Overview](#overview)
- [Protocol](#protocol)
- [HTTP Endpoints](#http-endpoints)
- [gRPC API](#grpc-api)
- [Error Codes](#error-codes)
- [Examples](#examples)

---

## Overview

The Order Service manages the complete order lifecycle from creation through fulfillment. It integrates with the Cart Service to validate cart items, the Catalog Service for product pricing, and Kafka for async event publishing.

**Base URL (HTTP):** `http://localhost:8085` (host-mapped)
**gRPC Target:** `localhost:50055` (host-mapped)

---

## Protocol

| Protocol | Port | Description |
|----------|------|-------------|
| HTTP (REST) | 8085 (host-mapped) | Order operations |
| gRPC | 50055 (host-mapped) | Service-to-service order operations |

---

## HTTP Endpoints

### Create Order

**POST** `/orders`

Create a new order from the user's shopping cart.

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| cart_id | string | Yes | UUID of the cart to convert |
| shipping_address | object | Yes | Shipping address details |
| payment_method | string | No | Payment method identifier |

**Shipping Address Object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| full_name | string | Yes | Full name |
| line1 | string | Yes | Address line 1 |
| line2 | string | No | Address line 2 |
| city | string | Yes | City |
| state | string | Yes | State/Province |
| postal_code | string | Yes | Postal code |
| country | string | Yes | Country code (ISO 3166-1) |
| phone | string | No | Contact phone |

#### Example Request

```bash
curl -X POST http://localhost:8085/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "cart_id": "cart_xyz789",
    "shipping_address": {
      "full_name": "John Doe",
      "line1": "123 Main St",
      "line2": "Apt 4B",
      "city": "New York",
      "state": "NY",
      "postal_code": "10001",
      "country": "US",
      "phone": "+1234567890"
    },
    "payment_method": "stripe_card"
  }'
```

#### Response (201 Created)

```json
{
  "id": "ord_def456",
  "user_id": "usr_abc123",
  "cart_id": "cart_xyz789",
  "status": "pending",
  "total_amount": 249.97,
  "currency": "USD",
  "items": [
    {
      "id": "item_001",
      "product_id": "prod_abc123",
      "product_name": "Wireless Headphones",
      "sku": "WH-001",
      "quantity": 1,
      "unit_price": 99.99,
      "total_price": 99.99,
      "image_url": "https://cdn.example.com/headphones.jpg"
    },
    {
      "id": "item_002",
      "product_id": "prod_def456",
      "product_name": "Phone Case",
      "sku": "PC-001",
      "quantity": 2,
      "unit_price": 74.99,
      "total_price": 149.98,
      "image_url": "https://cdn.example.com/case.jpg"
    }
  ],
  "shipping_address": {
    "full_name": "John Doe",
    "line1": "123 Main St",
    "line2": "Apt 4B",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "US",
    "phone": "+1234567890"
  },
  "payment_method": "stripe_card",
  "tracking_number": null,
  "created_at": "2026-08-03T10:00:00Z",
  "updated_at": "2026-08-03T10:00:00Z"
}
```

#### Error Responses

| Status | Detail |
|--------|--------|
| 400 | Invalid request body |
| 401 | Authentication required |
| 404 | Cart not found or empty |
| 422 | Insufficient stock |
| 502 | Cart or catalog service unavailable |
| 503 | Service unavailable |

---

### Get Order

**GET** `/orders/{order_id}`

Retrieve order details by ID.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| order_id | string | Order UUID |

#### Example Request

```bash
curl http://localhost:8085/orders/ord_def456 \
  -H "Authorization: Bearer <access_token>"
```

#### Response (200 OK)

```json
{
  "id": "ord_def456",
  "user_id": "usr_abc123",
  "cart_id": "cart_xyz789",
  "status": "processing",
  "total_amount": 249.97,
  "currency": "USD",
  "items": [...],
  "shipping_address": {...},
  "payment_method": "stripe_card",
  "tracking_number": "1Z999AA10123456784",
  "created_at": "2026-08-03T10:00:00Z",
  "updated_at": "2026-08-03T11:00:00Z",
  "completed_at": null,
  "cancelled_at": null
}
```

#### Error Responses

| Status | Detail |
|--------|--------|
| 401 | Authentication required |
| 404 | Order not found |
| 403 | Order does not belong to user |

---

### Get User Orders

**GET** `/orders`

Retrieve paginated order history for the authenticated user.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | integer | 1 | Page number (1-based) |
| page_size | integer | 20 | Items per page (1-100) |
| status | string | null | Filter by status |

#### Example Request

```bash
curl "http://localhost:8085/orders?page=1&page_size=10&status=processing" \
  -H "Authorization: Bearer <access_token>"
```

#### Response (200 OK)

```json
{
  "orders": [
    {
      "id": "ord_def456",
      "status": "processing",
      "total_amount": 249.97,
      "currency": "USD",
      "item_count": 2,
      "created_at": "2026-08-03T10:00:00Z"
    },
    {
      "id": "ord_ghi789",
      "status": "delivered",
      "total_amount": 49.99,
      "currency": "USD",
      "item_count": 1,
      "created_at": "2026-07-28T14:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 25,
    "total_pages": 3
  }
}
```

---

### Cancel Order

**POST** `/orders/{order_id}/cancel`

Cancel a pending or processing order.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| order_id | string | Order UUID |

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| reason | string | Yes | Reason for cancellation |

#### Example Request

```bash
curl -X POST http://localhost:8085/orders/ord_def456/cancel \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "reason": "Changed my mind"
  }'
```

#### Response (200 OK)

```json
{
  "success": true,
  "message": "Order cancelled successfully",
  "order_id": "ord_def456",
  "new_status": "cancelled"
}
```

#### Error Responses

| Status | Detail |
|--------|--------|
| 400 | Order cannot be cancelled (already shipped) |
| 401 | Authentication required |
| 404 | Order not found |
| 403 | Order does not belong to user |

---

## gRPC API

### Service Definition

```protobuf
service OrderService {
  // CreateOrder creates a new order from a cart.
  rpc CreateOrder(CreateOrderRequest) returns (Order);

  // GetOrder retrieves order details by ID.
  rpc GetOrder(GetOrderRequest) returns (Order);

  // GetUserOrders returns paginated list of orders for a user.
  rpc GetUserOrders(GetUserOrdersRequest) returns (GetUserOrdersResponse);

  // CancelOrder cancels a pending or processing order.
  rpc CancelOrder(CancelOrderRequest) returns (CancelOrderResponse);

  // UpdateOrderStatus updates the status of an order.
  rpc UpdateOrderStatus(UpdateOrderStatusRequest) returns (Order);
}
```

### Message Types

#### Order

```protobuf
message Order {
  string id = 1;
  string user_id = 2;
  string cart_id = 3;
  string status = 4;
  double total_amount = 5;
  string currency = 6;
  repeated OrderItem items = 7;
  ShippingAddress shipping_address = 8;
  string payment_method = 9;
  string tracking_number = 10;
  string cancelled_by = 11;
  string cancellation_reason = 12;
  int64 created_at = 13;
  int64 updated_at = 14;
  int64 completed_at = 15;
  int64 cancelled_at = 16;
}
```

#### OrderItem

```protobuf
message OrderItem {
  string id = 1;
  string product_id = 2;
  string product_name = 3;
  string sku = 4;
  int32 quantity = 5;
  double unit_price = 6;
  double total_price = 7;
  string image_url = 8;
}
```

#### ShippingAddress

```protobuf
message ShippingAddress {
  string full_name = 1;
  string line1 = 2;
  string line2 = 3;
  string city = 4;
  string state = 5;
  string postal_code = 6;
  string country = 7;
  string phone = 8;
}
```

#### CreateOrderRequest

```protobuf
message CreateOrderRequest {
  string user_id = 1;
  string cart_id = 2;
  ShippingAddress shipping_address = 3;
  string payment_method = 4;
}
```

#### GetOrderRequest

```protobuf
message GetOrderRequest {
  string order_id = 1;
}
```

#### GetUserOrdersRequest

```protobuf
message GetUserOrdersRequest {
  string user_id = 1;
  int32 page = 2;
  int32 page_size = 3;
  string status = 4;
}
```

#### GetUserOrdersResponse

```protobuf
message GetUserOrdersResponse {
  repeated Order orders = 1;
  Pagination pagination = 2;
}
```

#### CancelOrderRequest

```protobuf
message CancelOrderRequest {
  string order_id = 1;
  string user_id = 2;
  string reason = 3;
}
```

#### CancelOrderResponse

```protobuf
message CancelOrderResponse {
  bool success = 1;
  string message = 2;
}
```

#### UpdateOrderStatusRequest

```protobuf
message UpdateOrderStatusRequest {
  string order_id = 1;
  string status = 2;
}
```

### gRPC Examples

#### Python — Create Order

```python
import grpc
import order_pb2
import order_pb2_grpc

channel = grpc.insecure_channel('localhost:50055')
stub = order_pb2_grpc.OrderServiceStub(channel)

# Create order
response = stub.CreateOrder(
    order_pb2.CreateOrderRequest(
        user_id='usr_abc123',
        cart_id='cart_xyz789',
        shipping_address=order_pb2.ShippingAddress(
            full_name='John Doe',
            line1='123 Main St',
            city='New York',
            state='NY',
            postal_code='10001',
            country='US',
            phone='+1234567890'
        ),
        payment_method='stripe_card'
    )
)
print(f"Order created: {response.id}")
print(f"Total: ${response.total_amount} {response.currency}")
```

#### Python — Get Order

```python
# Get order
response = stub.GetOrder(
    order_pb2.GetOrderRequest(order_id='ord_def456')
)
print(f"Status: {response.status}")
print(f"Tracking: {response.tracking_number}")
```

---

## Order Status Flow

```
     pending
        │
        ▼
   processing  ──►  shipped  ──►  delivered
        │
        ▼
     cancelled
```

| Status | Description |
|--------|-------------|
| `pending` | Order created, awaiting payment |
| `processing` | Payment confirmed, being prepared |
| `shipped` | Order shipped with tracking |
| `delivered` | Order delivered to customer |
| `cancelled` | Order cancelled by user or admin |

---

## Error Codes

| HTTP Status | Description |
|-------------|-------------|
| 400 | Invalid request parameters |
| 401 | Authentication required |
| 404 | Order or cart not found |
| 409 | Order already cancelled |
| 422 | Invalid operation for current status |
| 502 | Cart or catalog service unavailable |
| 503 | Service unavailable |

| gRPC Status | Description |
|-------------|-------------|
| `INVALID_ARGUMENT` | Invalid request parameters |
| `NOT_FOUND` | Order or cart not found |
| `FAILED_PRECONDITION` | Invalid operation for status |
| `UNAVAILABLE` | Dependent service unavailable |
| `INTERNAL` | Internal server error |

---

## Kafka Events

### order.created

Published when a new order is created.

```json
{
  "event_type": "order.created",
  "order_id": "ord_def456",
  "user_id": "usr_abc123",
  "total_amount": 249.97,
  "currency": "USD",
  "item_count": 2,
  "created_at": "2026-08-03T10:00:00Z"
}
```

### order.status_changed

Published when order status changes.

```json
{
  "event_type": "order.status_changed",
  "order_id": "ord_def456",
  "user_id": "usr_abc123",
  "old_status": "pending",
  "new_status": "processing",
  "changed_at": "2026-08-03T10:05:00Z"
}
```

---

## Examples

### Complete Order Flow

```bash
# 1. Create order from cart
ORDER=$(curl -s -X POST http://localhost:8085/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "cart_id": "cart_xyz789",
    "shipping_address": {
      "full_name": "John Doe",
      "line1": "123 Main St",
      "city": "New York",
      "state": "NY",
      "postal_code": "10001",
      "country": "US"
    },
    "payment_method": "stripe_card"
  }')

echo $ORDER

# 2. Get order details
curl -s http://localhost:8085/orders/ord_def456 \
  -H "Authorization: Bearer $TOKEN"

# 3. Cancel order (if pending)
curl -s -X POST http://localhost:8085/orders/ord_def456/cancel \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"reason": "Changed my mind"}'

# 4. Get order history
curl -s "http://localhost:8085/orders?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Related Documentation

- [Services Overview](services.md) — Service architecture
- [gRPC API Reference](grpc-api.md) — Full proto definitions
- [Kafka Events](../kafka.md) — Event streaming details
- [Payment Service](payment-service.md) — Payment integration
