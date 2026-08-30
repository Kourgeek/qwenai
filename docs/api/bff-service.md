# BFF Service API Documentation

Backend-for-Frontend service providing aggregated data endpoints for client applications.

---

## Table of Contents

- [Overview](#overview)
- [Protocol](#protocol)
- [Endpoints](#endpoints)
- [Error Codes](#error-codes)
- [Examples](#examples)

---

## Overview

The BFF (Backend-for-Frontend) Service aggregates data from multiple microservices into single responses optimized for client applications. It reduces the number of round trips clients need to make by combining data from catalog, search, cart, order, payment, user, seller, and notification services.

**Base URL (HTTP):** `http://localhost:8089` (host-mapped)
**gRPC Target:** `localhost:50059` (host-mapped)

---

## Protocol

| Protocol | Port | Description |
|----------|------|-------------|
| HTTP (REST) | 8089 (host-mapped) | Client-facing aggregation endpoints |
| gRPC | 50059 (host-mapped) | Internal service-to-service aggregation |

### Architecture

```
Client                    BFF Service              Backend Services
  │                           │                        │
  │  GET /bff/profile         │                        │
  │──────────────────────────>│                        │
  │                           ├──► user-service (gRPC)  │
  │                           ├──► cart-service (gRPC)  │
  │                           └──► notification-svc     │
  │                           │                        │
  │  {aggregated response}   │                        │
  │<──────────────────────────│                        │
  │                           │                        │
  │  GET /bff/search          │                        │
  │──────────────────────────>│                        │
  │                           ├──► search-service       │
  │                           └──► catalog-service      │
  │                           │                        │
  │  {aggregated response}   │                        │
  │<──────────────────────────│                        │
```

---

## Endpoints

### Get User Profile

**GET** `/bff/profile`

Aggregate user profile data from multiple services.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | string | Yes | User UUID |

#### Example Request

```bash
curl "http://localhost:8089/bff/profile?user_id=usr_abc123" \
  -H "Authorization: Bearer <access_token>"
```

#### Response (200 OK)

```json
{
  "user": {
    "id": "usr_abc123",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "avatar_url": "https://cdn.example.com/avatars/user.jpg",
    "role": "user",
    "created_at": "2026-01-15T10:00:00Z"
  },
  "addresses": [
    {
      "id": "addr_001",
      "full_name": "John Doe",
      "line1": "123 Main St",
      "line2": "Apt 4B",
      "city": "New York",
      "state": "NY",
      "postal_code": "10001",
      "country": "US",
      "is_default": true
    }
  ],
  "wishlist": [
    {
      "id": "wish_001",
      "product_id": "prod_def456",
      "product_name": "Smart Watch",
      "image_url": "https://cdn.example.com/watch.jpg",
      "price": 199.99,
      "currency": "USD",
      "added_at": "2026-07-20T14:00:00Z"
    }
  ]
}
```

---

### Get Shopping Cart

**GET** `/bff/cart`

Retrieve the user's shopping cart with live pricing from the catalog service.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | string | Yes | User UUID |

#### Example Request

```bash
curl "http://localhost:8089/bff/cart?user_id=usr_abc123" \
  -H "Authorization: Bearer <access_token>"
```

#### Response (200 OK)

```json
{
  "cart_id": "cart_xyz789",
  "items": [
    {
      "id": "item_001",
      "product_id": "prod_abc123",
      "product_name": "Wireless Headphones",
      "sku": "WH-001",
      "quantity": 1,
      "unit_price": 99.99,
      "total_price": 99.99,
      "image_url": "https://cdn.example.com/headphones.jpg",
      "is_available": true
    },
    {
      "id": "item_002",
      "product_id": "prod_def456",
      "product_name": "Phone Case",
      "sku": "PC-001",
      "quantity": 2,
      "unit_price": 74.99,
      "total_price": 149.98,
      "image_url": "https://cdn.example.com/case.jpg",
      "is_available": true
    }
  ],
  "subtotal": 249.97,
  "shipping_cost": 9.99,
  "total": 259.96,
  "currency": "USD"
}
```

---

### Get Order History

**GET** `/bff/orders`

Retrieve the user's order history with item details.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| user_id | string | — | User UUID (required) |
| limit | integer | 20 | Max results (1-100) |
| offset | integer | 0 | Pagination offset |

#### Example Request

```bash
curl "http://localhost:8089/bff/orders?user_id=usr_abc123&limit=10&offset=0" \
  -H "Authorization: Bearer <access_token>"
```

#### Response (200 OK)

```json
{
  "orders": [
    {
      "id": "ord_def456",
      "user_id": "usr_abc123",
      "status": "processing",
      "total_amount": 249.97,
      "currency": "USD",
      "item_count": 2,
      "shipping_address": {
        "full_name": "John Doe",
        "line1": "123 Main St",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "US"
      },
      "payment_method": "stripe_card",
      "tracking_number": "1Z999AA10123456784",
      "created_at": "2026-08-03T10:00:00Z",
      "updated_at": "2026-08-03T11:00:00Z"
    },
    {
      "id": "ord_ghi789",
      "user_id": "usr_abc123",
      "status": "delivered",
      "total_amount": 49.99,
      "currency": "USD",
      "item_count": 1,
      "created_at": "2026-07-28T14:00:00Z",
      "updated_at": "2026-08-01T09:00:00Z"
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

### Search Products

**GET** `/bff/search`

Aggregate product search results from the search service with enriched data.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| q | string | — | Search query (required) |
| limit | integer | 20 | Max results (1-100) |
| offset | integer | 0 | Pagination offset |
| category_id | string | null | Filter by category |
| min_price | number | null | Minimum price filter |
| max_price | number | null | Maximum price filter |
| sort_by | string | relevance | Sort field (`relevance`, `price_asc`, `price_desc`, `newest`) |

#### Example Request

```bash
curl "http://localhost:8089/bff/search?q=wireless+headphones&limit=10&sort_by=price_asc&min_price=50&max_price=200" \
  -H "Authorization: Bearer <access_token>"
```

#### Response (200 OK)

```json
{
  "products": [
    {
      "id": "prod_abc123",
      "name": "Wireless Headphones",
      "description": "Premium noise-cancelling wireless headphones",
      "price": 99.99,
      "compare_at_price": 149.99,
      "currency": "USD",
      "category": "Electronics",
      "brand": "AudioTech",
      "quantity": 100,
      "image_url": "https://cdn.example.com/headphones.jpg",
      "avg_rating": 4.5,
      "review_count": 128,
      "seller_id": "seller_001",
      "seller_name": "AudioTech Official",
      "is_active": true,
      "created_at": "2026-06-15T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 42,
    "total_pages": 5
  },
  "took_ms": 15
}
```

---

### Get Seller Profile

**GET** `/bff/seller/{seller_id}`

Retrieve seller information with product listing.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| seller_id | string | Seller UUID |

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | integer | 1 | Page number |
| page_size | integer | 20 | Items per page |

#### Example Request

```bash
curl "http://localhost:8089/bff/seller/seller_001?page=1&page_size=10" \
  -H "Authorization: Bearer <access_token>"
```

#### Response (200 OK)

```json
{
  "seller": {
    "id": "seller_001",
    "name": "AudioTech Official",
    "description": "Official store for AudioTech products",
    "logo_url": "https://cdn.example.com/sellers/audiotech-logo.jpg",
    "avg_rating": 4.7,
    "product_count": 156,
    "total_reviews": 2340,
    "is_verified": true,
    "created_at": "2025-01-01T00:00:00Z"
  },
  "products": [
    {
      "id": "prod_abc123",
      "name": "Wireless Headphones",
      "price": 99.99,
      "image_url": "https://cdn.example.com/headphones.jpg",
      "avg_rating": 4.5
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 156,
    "total_pages": 16
  }
}
```

---

### Get User Notifications

**GET** `/bff/notifications`

Retrieve user notifications from the notification service.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| user_id | string | — | User UUID (required) |
| page | integer | 1 | Page number |
| page_size | integer | 20 | Items per page |
| unread_only | boolean | false | Only unread notifications |

#### Example Request

```bash
curl "http://localhost:8089/bff/notifications?user_id=usr_abc123&page=1&page_size=10&unread_only=true"
```

#### Response (200 OK)

```json
{
  "notifications": [
    {
      "id": "notif_001",
      "user_id": "usr_abc123",
      "title": "Order Shipped",
      "message": "Your order ord_def456 has been shipped",
      "type": "order_shipped",
      "is_read": false,
      "created_at": "2026-08-03T12:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 5,
    "total_pages": 1
  },
  "unread_count": 3
}
```

---

### Get Dashboard Stats (Admin)

**GET** `/bff/admin/dashboard`

Retrieve marketplace dashboard statistics.

#### Example Request

```bash
curl http://localhost:8089/bff/admin/dashboard \
  -H "Authorization: Bearer <admin_token>"
```

#### Response (200 OK)

```json
{
  "total_users": 15420,
  "total_products": 8934,
  "total_orders": 45230,
  "total_revenue": 2450000.00,
  "active_sellers": 342,
  "orders_today": 156,
  "revenue_today": 12500.00,
  "revenue_growth_rate": 12.5
}
```

---

## gRPC API

### Service Definition

```protobuf
service BffService {
  // GetProductCatalog aggregates catalog, search, review/rating data.
  rpc GetProductCatalog(ProductCatalogRequest) returns (ProductCatalogResponse);

  // GetProductDetails aggregates product, seller, delivery data.
  rpc GetProductDetails(ProductDetailsRequest) returns (ProductDetailsResponse);

  // GetCartWithPrices fetches cart items with live pricing.
  rpc GetCartWithPrices(CartWithPricesRequest) returns (CartWithPricesResponse);

  // Checkout aggregates cart, order, payment, notification events.
  rpc Checkout(CheckoutRequest) returns (CheckoutResponse);

  // GetOrderHistory aggregates order history with item details.
  rpc GetOrderHistory(GetOrderHistoryRequest) returns (GetOrderHistoryResponse);

  // GetUserProfile aggregates user profile, addresses, wishlist.
  rpc GetUserProfile(GetUserProfileRequest) returns (UserProfileResponse);

  // GetSellerProfile aggregates seller profile and products.
  rpc GetSellerProfile(GetSellerProfileRequest) returns (SellerProfileResponse);

  // GetUserNotifications fetches user notifications.
  rpc GetUserNotifications(GetUserNotificationsRequest) returns (UserNotificationsResponse);
}
```

### Key Message Types

#### Product

```protobuf
message Product {
  string id = 1;
  string name = 2;
  string description = 3;
  float price = 4;
  string currency = 5;
  string category = 6;
  string brand = 7;
  int32 quantity = 8;
  string image_url = 9;
  float avg_rating = 10;
  int32 review_count = 11;
  string seller_id = 12;
  string seller_name = 13;
  bool is_active = 14;
  int64 created_at = 15;
}
```

#### CartItem

```protobuf
message CartItem {
  string id = 1;
  string product_id = 2;
  string product_name = 3;
  string sku = 4;
  int32 quantity = 5;
  float unit_price = 6;
  float total_price = 7;
  string image_url = 8;
  bool is_available = 9;
}
```

#### CheckoutRequest

```protobuf
message CheckoutRequest {
  string user_id = 1;
  string cart_id = 2;
  ShippingAddress shipping_address = 3;
  string payment_method = 4;
}
```

#### CheckoutResponse

```protobuf
message CheckoutResponse {
  string order_id = 1;
  string status = 2;
  float total_amount = 3;
  string currency = 4;
  int64 created_at = 5;
}
```

#### Pagination

```protobuf
message Pagination {
  int32 page = 1;
  int32 page_size = 2;
  int32 total = 3;
  int32 total_pages = 4;
}
```

---

## Error Codes

| HTTP Status | Description |
|-------------|-------------|
| 400 | Invalid request parameters |
| 401 | Authentication required |
| 404 | Resource not found |
| 502 | Backend service unavailable |
| 503 | BFF service unavailable |

---

## Examples

### Full Product Detail Flow

```bash
# 1. Search for products
curl -s "http://localhost:8089/bff/search?q=headphones&limit=5" \
  -H "Authorization: Bearer $TOKEN"

# 2. Get seller info
curl -s "http://localhost:8089/bff/seller/seller_001" \
  -H "Authorization: Bearer $TOKEN"

# 3. Get user profile
curl -s "http://localhost:8089/bff/profile?user_id=usr_abc123" \
  -H "Authorization: Bearer $TOKEN"

# 4. Get cart
curl -s "http://localhost:8089/bff/cart?user_id=usr_abc123" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Related Documentation

- [Services Overview](services.md) — Service architecture
- [Gateway Documentation](gateway.md) — API gateway routing
- [gRPC API Reference](grpc-api.md) — Full proto definitions
