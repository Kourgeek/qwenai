# API Documentation Index

Central navigation for all HyperScale Marketplace API documentation.

---

## Table of Contents

- [Authentication](#authentication)
- [Gateway](#gateway)
- [Services](#services)
- [Service API Docs](#service-api-docs)
- [gRPC API Reference](#grpc-api-reference)
- [Kafka Events](#kafka-events)

---

## Authentication

[docs/authentication.md](authentication.md)

- JWT authentication flow
- API key authentication
- Token refresh mechanism
- Security best practices

---

## Gateway

[docs/gateway.md](gateway.md)

- Route table
- Rate limiting configuration
- CORS settings
- Request/response transformation
- Circuit breaker pattern

---

## Services

[docs/services.md](services.md)

- Service overview table
- Service dependency graph
- Communication patterns
- Data flow diagrams

---

## Service API Docs

### Auth Service

[docs/api/auth-service.md](api/auth-service.md)

- **Protocol:** gRPC + HTTP
- **Port:** gRPC 50051 (host), HTTP (internal)
- **Endpoints:**
  - `POST /auth/login` — User login
  - `POST /auth/register` — User registration
  - `POST /auth/refresh` — Token refresh
  - `POST /auth/logout` — Token invalidation
  - `POST /auth/forgot-password` — Password reset

### Catalog Service

[docs/api/catalog-service.md](api/catalog-service.md)

- **Protocol:** HTTP + gRPC
- **HTTP Port:** 8084 (host)
- **gRPC Port:** 50053 (host)
- **Endpoints:**
  - Products: CRUD + search
  - Categories: CRUD + tree
  - Brands: CRUD + search
  - Tags: CRUD

### Order Service

[docs/api/order-service.md](api/order-service.md)

- **Protocol:** gRPC + HTTP
- **Port:** gRPC 50055 (host), HTTP 8085 (host)
- **Endpoints:**
  - `CreateOrder` — Create order from cart
  - `GetOrder` — Retrieve order by ID
  - `GetUserOrders` — Paginated order history
  - `CancelOrder` — Cancel pending order
  - `UpdateOrderStatus` — Update order status

### Payment Service

[docs/api/payment-service.md](api/payment-service.md)

- **Protocol:** HTTP + gRPC
- **HTTP Port:** 8082 (host)
- **gRPC Port:** 50056 (host)
- **Endpoints:**
  - `CreatePayment` — Create payment intent
  - `ConfirmPayment` — Confirm payment
  - `GetPayment` — Retrieve payment details
  - `RefundPayment` — Process refund
  - `GetUserPayments` — Payment history
  - Webhooks: Stripe + YooMoney

### BFF Service

[docs/api/bff-service.md](api/bff-service.md)

- **Protocol:** HTTP
- **Port:** 8089 (host)
- **Endpoints:**
  - `GET /bff/profile` — User profile aggregation
  - `GET /bff/cart` — Shopping cart with pricing
  - `GET /bff/orders` — Order history
  - `GET /bff/search` — Product search
  - `GET /bff/seller/{id}` — Seller info
  - `GET /bff/admin/dashboard` — Dashboard stats

---

## gRPC API Reference

[docs/grpc-api.md](grpc-api.md)

Complete gRPC API documentation covering all protocol buffer definitions:

| Service | Package | Proto File |
|---------|---------|------------|
| AuthService | auth.v1 | `proto/auth/v1/auth.proto` |
| UserService | user.v1 | `proto/user/v1/user.proto` |
| CatalogService | catalog.v1 | `proto/catalog/v1/catalog.proto` |
| CartService | cart.v1 | `proto/cart/v1/cart.proto` |
| OrderService | order.v1 | `proto/order/v1/order.proto` |
| PaymentService | payment.v1 | `proto/payment/v1/payment.proto` |
| NotificationService | notification.v1 | `proto/notification/v1/notification.proto` |
| SearchService | search.v1 | `proto/search/v1/search.proto` |
| SellerService | seller.v1 | `proto/seller/v1/seller.proto` |
| BffService | bff.v1 | `proto/bff/v1/bff.proto` |

---

## Kafka Events

[docs/kafka.md](kafka.md)

- Topic schemas and message formats
- Producer/consumer patterns
- Event sourcing architecture
- Data flow documentation

---

## Quick Links

| Document | Description |
|----------|-------------|
| [Development Guide](development.md) | Local setup, testing, code style |
| [Deployment Guide](deployment.md) | Production deployment, K8s, SSL |
| [Monitoring Guide](monitoring.md) | Prometheus, Grafana, alerting |
| [Main README](../README.md) | Project overview and quick start |
