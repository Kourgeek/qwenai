# Payment Service API Documentation

Payment processing service supporting Stripe and YooMoney payment providers.

---

## Table of Contents

- [Overview](#overview)
- [Protocol](#protocol)
- [HTTP Endpoints](#http-endpoints)
- [gRPC API](#grpc-api)
- [Webhooks](#webhooks)
- [Error Codes](#error-codes)
- [Examples](#examples)

---

## Overview

The Payment Service handles payment processing for marketplace orders. It supports multiple payment providers (Stripe, YooMoney) and manages the full payment lifecycle including creation, confirmation, refunds, and webhook handling.

**Base URL (HTTP):** `http://localhost:8082` (host-mapped)
**gRPC Target:** `localhost:50056` (host-mapped)

---

## Protocol

| Protocol | Port | Description |
|----------|------|-------------|
| HTTP (REST) | 8082 (host-mapped) | Payment operations, webhooks |
| gRPC | 50056 (host-mapped) | Service-to-service payment operations |

---

## HTTP Endpoints

### Create Payment

**POST** `/payments`

Create a new payment intent for an order.

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| order_id | string | Yes | Order UUID |
| user_id | string | Yes | User UUID |
| payment_method_id | string | No | Saved payment method ID |
| currency | string | No | Currency code (default: RUB) |
| amount | integer | Yes | Amount in cents/smallest unit |
| provider | string | No | Payment provider (`stripe`, `yoomoney`) |

#### Example Request

```bash
curl -X POST http://localhost:8082/payments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "order_id": "ord_def456",
    "user_id": "usr_abc123",
    "payment_method_id": "pm_card_visa",
    "currency": "USD",
    "amount": 24997,
    "provider": "stripe"
  }'
```

#### Response (201 Created)

```json
{
  "id": "pay_ghi789",
  "order_id": "ord_def456",
  "user_id": "usr_abc123",
  "amount": 24997,
  "currency": "USD",
  "status": "pending",
  "provider": "stripe",
  "provider_payment_id": "pi_1234567890",
  "checkout_url": "https://checkout.stripe.com/pay/abc123",
  "created_at": "2026-08-03T10:00:00Z",
  "updated_at": "2026-08-03T10:00:00Z"
}
```

#### Error Responses

| Status | Detail |
|--------|--------|
| 400 | Invalid request body |
| 401 | Authentication required |
| 404 | Order not found |
| 422 | Invalid payment method |
| 502 | Payment provider error |
| 503 | Service unavailable |

---

### Confirm Payment

**POST** `/payments/{payment_id}/confirm`

Confirm a pending payment after provider callback.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| payment_id | string | Payment UUID |

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| provider_data | object | Yes | Provider-specific confirmation data |

#### Example Request

```bash
curl -X POST http://localhost:8082/payments/pay_ghi789/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "provider_data": {
      "payment_intent_id": "pi_1234567890",
      "status": "succeeded"
    }
  }'
```

#### Response (200 OK)

```json
{
  "id": "pay_ghi789",
  "order_id": "ord_def456",
  "status": "completed",
  "provider_payment_id": "pi_1234567890",
  "paid_at": "2026-08-03T10:05:00Z",
  "updated_at": "2026-08-03T10:05:00Z"
}
```

---

### Get Payment

**GET** `/payments/{payment_id}`

Retrieve payment details.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| payment_id | string | Payment UUID |

#### Example Request

```bash
curl http://localhost:8082/payments/pay_ghi789 \
  -H "Authorization: Bearer <access_token>"
```

#### Response (200 OK)

```json
{
  "id": "pay_ghi789",
  "order_id": "ord_def456",
  "user_id": "usr_abc123",
  "amount": 24997,
  "currency": "USD",
  "status": "completed",
  "provider": "stripe",
  "provider_payment_id": "pi_1234567890",
  "payment_method_id": "pm_card_visa",
  "created_at": "2026-08-03T10:00:00Z",
  "updated_at": "2026-08-03T10:05:00Z",
  "paid_at": "2026-08-03T10:05:00Z"
}
```

---

### Refund Payment

**POST** `/payments/{payment_id}/refund`

Process a refund for a completed payment.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| payment_id | string | Payment UUID |

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| amount | integer | No | Refund amount (default: full refund) |
| reason | string | Yes | Reason for refund |

#### Example Request

```bash
curl -X POST http://localhost:8082/payments/pay_ghi789/refund \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "amount": 9999,
    "reason": "Product returned"
  }'
```

#### Response (200 OK)

```json
{
  "id": "ref_jkl012",
  "payment_id": "pay_ghi789",
  "user_id": "usr_abc123",
  "amount": 9999,
  "currency": "USD",
  "status": "processing",
  "provider_refund_id": "re_1234567890",
  "reason": "Product returned",
  "created_at": "2026-08-03T11:00:00Z"
}
```

---

### Get User Payments

**GET** `/payments`

Retrieve payment history for a user.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| user_id | string | — | User UUID (required) |
| page | integer | 1 | Page number |
| page_size | integer | 20 | Items per page |
| status_filter | string | null | Filter by status |

#### Example Request

```bash
curl "http://localhost:8082/payments?user_id=usr_abc123&page=1&page_size=10&status_filter=completed" \
  -H "Authorization: Bearer <access_token>"
```

#### Response (200 OK)

```json
{
  "payments": [
    {
      "id": "pay_ghi789",
      "order_id": "ord_def456",
      "amount": 24997,
      "currency": "USD",
      "status": "completed",
      "provider": "stripe",
      "created_at": "2026-08-03T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 5
  }
}
```

---

## gRPC API

### Service Definition

```protobuf
service PaymentService {
  rpc CreatePayment(CreatePaymentRequest) returns (Payment);
  rpc ConfirmPayment(ConfirmPaymentRequest) returns (Payment);
  rpc GetPayment(GetPaymentRequest) returns (Payment);
  rpc RefundPayment(RefundPaymentRequest) returns (Refund);
  rpc GetUserPayments(GetUserPaymentsRequest) returns (PaymentList);
  rpc Webhook(WebhookRequest) returns (WebhookResponse);
}
```

### Message Types

#### Payment

```protobuf
message Payment {
  string id = 1;
  string order_id = 2;
  string user_id = 3;
  int64 amount = 4;
  string currency = 5;
  PaymentStatus status = 6;
  PaymentProvider provider = 7;
  string provider_payment_id = 8;
  string provider_error = 9;
  string payment_method_id = 10;
  Timestamp created_at = 11;
  Timestamp updated_at = 12;
  Timestamp paid_at = 13;
}
```

#### PaymentStatus Enum

```protobuf
enum PaymentStatus {
  PAYMENT_STATUS_UNSPECIFIED = 0;
  PAYMENT_STATUS_PENDING = 1;
  PAYMENT_STATUS_CREATED = 2;
  PAYMENT_STATUS_PROCESSING = 3;
  PAYMENT_STATUS_COMPLETED = 4;
  PAYMENT_STATUS_FAILED = 5;
  PAYMENT_STATUS_REFUNDED = 6;
  PAYMENT_STATUS_PARTIALLY_REFUNDED = 7;
  PAYMENT_STATUS_CANCELLED = 8;
}
```

#### PaymentProvider Enum

```protobuf
enum PaymentProvider {
  PAYMENT_PROVIDER_UNSPECIFIED = 0;
  PAYMENT_PROVIDER_STRIPE = 1;
  PAYMENT_PROVIDER_YOOMONEY = 2;
}
```

#### PaymentMethodType Enum

```protobuf
enum PaymentMethodType {
  PAYMENT_METHOD_TYPE_UNSPECIFIED = 0;
  PAYMENT_METHOD_TYPE_CARD = 1;
  PAYMENT_METHOD_TYPE_BANK_TRANSFER = 2;
  PAYMENT_METHOD_TYPE_E_WALLET = 3;
  PAYMENT_METHOD_TYPE_CRYPTO = 4;
}
```

#### PaymentList

```protobuf
message PaymentList {
  repeated Payment payments = 1;
  Pagination pagination = 2;
}
```

#### Refund

```protobuf
message Refund {
  string id = 1;
  string payment_id = 2;
  string user_id = 3;
  int64 amount = 4;
  string currency = 5;
  string status = 6;
  string provider_refund_id = 7;
  string reason = 8;
  Timestamp created_at = 9;
  Timestamp refunded_at = 10;
}
```

#### CreatePaymentRequest

```protobuf
message CreatePaymentRequest {
  string order_id = 1;
  string user_id = 2;
  string payment_method_id = 3;
  string currency = 4;
  int64 amount = 5;
  PaymentProvider provider = 6;
}
```

#### ConfirmPaymentRequest

```protobuf
message ConfirmPaymentRequest {
  string payment_id = 1;
  map<string, string> provider_data = 2;
}
```

#### GetPaymentRequest

```protobuf
message GetPaymentRequest {
  string payment_id = 1;
}
```

#### RefundPaymentRequest

```protobuf
message RefundPaymentRequest {
  string payment_id = 1;
  int64 amount = 2;
  string reason = 3;
}
```

#### GetUserPaymentsRequest

```protobuf
message GetUserPaymentsRequest {
  string user_id = 1;
  int32 page = 2;
  int32 page_size = 3;
  PaymentStatus status_filter = 4;
}
```

#### WebhookRequest

```protobuf
message WebhookRequest {
  string event_type = 1;
  map<string, string> payload = 2;
}
```

#### WebhookResponse

```protobuf
message WebhookResponse {
  bool success = 1;
  string message = 2;
}
```

### gRPC Examples

#### Python — Create Payment

```python
import grpc
import payment_pb2
import payment_pb2_grpc

channel = grpc.insecure_channel('localhost:50056')
stub = payment_pb2_grpc.PaymentServiceStub(channel)

# Create payment
response = stub.CreatePayment(
    payment_pb2.CreatePaymentRequest(
        order_id='ord_def456',
        user_id='usr_abc123',
        payment_method_id='pm_card_visa',
        currency='USD',
        amount=24997,
        provider=payment_pb2.PAYMENT_PROVIDER_STRIPE
    )
)
print(f"Payment created: {response.id}")
print(f"Checkout URL: {response.checkout_url}")
```

#### Python — Confirm Payment

```python
# Confirm payment
response = stub.ConfirmPayment(
    payment_pb2.ConfirmPaymentRequest(
        payment_id='pay_ghi789',
        provider_data={'payment_intent_id': 'pi_1234567890'}
    )
)
print(f"Status: {response.status}")
```

---

## Webhooks

### Stripe Webhook

**POST** `/webhook/stripe`

Handles Stripe payment events.

#### Required Headers

| Header | Description |
|--------|-------------|
| `stripe-signature` | Stripe signature for verification |

#### Example Request

```bash
curl -X POST http://localhost:8082/webhook/stripe \
  -H "Content-Type: application/json" \
  -H "stripe-signature: sig_abc123" \
  -d '{
    "id": "evt_123456",
    "type": "payment_intent.succeeded",
    "data": {
      "object": {
        "id": "pi_1234567890",
        "amount": 24997,
        "currency": "usd",
        "status": "succeeded"
      }
    }
  }'
```

#### Response

```json
{
  "success": true,
  "message": "Webhook processed successfully"
}
```

### YooMoney Webhook

**POST** `/webhook/yoomoney`

Handles YooMoney payment events.

#### Required Headers

| Header | Description |
|--------|-------------|
| `X-Notification-Checksum` | HMAC signature for verification |

#### Example Request

```bash
curl -X POST http://localhost:8082/webhook/yoomoney \
  -H "Content-Type: application/json" \
  -H "X-Notification-Checksum: sha256=abc123" \
  -d '{
    "event_type": "payment_succeeded",
    "order_id": "ord_def456",
    "amount": 24997,
    "currency": "RUB"
  }'
```

---

## Payment Status Flow

```
     pending
        │
        ▼
    created  ──►  processing  ──►  completed
        │                                    │
        ▼                                    ▼
     failed                         refunded
        │
        ▼
     cancelled
```

---

## Error Codes

| HTTP Status | Description |
|-------------|-------------|
| 400 | Invalid request body or webhook signature |
| 401 | Authentication required |
| 404 | Payment not found |
| 422 | Invalid payment method or amount |
| 502 | Payment provider error |
| 503 | Service unavailable |

| gRPC Status | Description |
|-------------|-------------|
| `INVALID_ARGUMENT` | Invalid request parameters |
| `NOT_FOUND` | Payment not found |
| `FAILED_PRECONDITION` | Invalid operation for status |
| `UNAVAILABLE` | Payment provider unavailable |
| `INTERNAL` | Internal server error |

---

## Examples

### Complete Payment Flow

```bash
# 1. Create payment intent
PAYMENT=$(curl -s -X POST http://localhost:8082/payments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "order_id": "ord_def456",
    "user_id": "usr_abc123",
    "amount": 24997,
    "currency": "USD",
    "provider": "stripe"
  }')

echo $PAYMENT
# {
#   "id": "pay_ghi789",
#   "checkout_url": "https://checkout.stripe.com/pay/abc123",
#   "status": "pending"
# }

# 2. Redirect user to checkout_url
# After payment, Stripe sends webhook to /webhook/stripe

# 3. Check payment status
curl -s http://localhost:8082/payments/pay_ghi789 \
  -H "Authorization: Bearer $TOKEN"

# 4. Process refund if needed
curl -s -X POST http://localhost:8082/payments/pay_ghi789/refund \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"amount": 24997, "reason": "Customer requested refund"}'
```

---

## Related Documentation

- [Services Overview](services.md) — Service architecture
- [gRPC API Reference](grpc-api.md) — Full proto definitions
- [Kafka Events](../kafka.md) — Payment events
- [Order Service](order-service.md) — Order payment integration
