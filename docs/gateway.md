# Gateway Documentation

The API Gateway is the single entry point for all external client requests. It handles authentication, rate limiting, CORS, request/response transformation, and circuit breaking before routing to backend services.

---

## Table of Contents

- [Architecture](#architecture)
- [Route Table](#route-table)
- [Rate Limiting](#rate-limiting)
- [CORS Configuration](#cors-configuration)
- [Request/Response Transformation](#requestresponse-transformation)
- [Circuit Breaker](#circuit-breaker)
- [Security Headers](#security-headers)
- [Configuration](#configuration)

---

## Architecture

```
Client Request
     │
     ▼
┌─────────────────────────────────────────┐
│              API Gateway                 │
│           (port 8080)                    │
│                                          │
│  1. Request ID Generation               │
│  2. CORS Pre-flight Handling            │
│  3. Rate Limiting (Redis-backed)        │
│  4. Authentication (JWT validation)     │
│  5. Request Validation                  │
│  6. Routing / Proxy                     │
│  7. Response Transformation             │
│  8. Security Headers                    │
└─────────────────────────────────────────┘
     │
     ├──► Auth Service (gRPC)
     ├──► BFF Service (HTTP :8085)
     ├──► Catalog Service (HTTP :8084)
     └──► Admin Service (HTTP :8085)
```

---

## Route Table

### Public Routes (No Authentication)

| Method | Path | Target | Description |
|--------|------|--------|-------------|
| `GET` | `/health` | Gateway | Health check |
| `POST` | `/auth/login` | Auth Service | User login |
| `POST` | `/auth/register` | Auth Service | User registration |
| `GET` | `/products` | BFF Service | Product listing |
| `GET` | `/products/search` | BFF Service | Product search |
| `GET` | `/categories` | Catalog Service | Category listing |
| `GET` | `/categories/{id}` | Catalog Service | Category detail |
| `GET` | `/brands` | Catalog Service | Brand listing |
| `GET` | `/brands/{id}` | Catalog Service | Brand detail |

### Authenticated Routes (Bearer Token Required)

| Method | Path | Target | Description |
|--------|------|--------|-------------|
| `POST` | `/cart` | BFF Service | Add item to cart |
| `GET` | `/cart` | BFF Service | Get shopping cart |
| `PUT` | `/cart/{product_id}` | BFF Service | Update cart item |
| `DELETE` | `/cart/{product_id}` | BFF Service | Remove from cart |
| `POST` | `/orders` | BFF Service | Create order |
| `GET` | `/orders/{id}` | BFF Service | Get order details |
| `GET` | `/orders` | BFF Service | Order history |
| `GET` | `/profile` | BFF Service | User profile |
| `POST` | `/auth/refresh` | Auth Service | Refresh token |
| `POST` | `/auth/logout` | Auth Service | Logout |

### Admin Routes (Admin Role Required)

| Method | Path | Target | Description |
|--------|------|--------|-------------|
| `GET` | `/admin/dashboard` | Admin Service | Dashboard stats |
| `GET` | `/admin/users` | Admin Service | User management |
| `PATCH` | `/admin/users/{id}` | Admin Service | Update user |
| `DELETE` | `/admin/users/{id}` | Admin Service | Delete user |
| `GET` | `/admin/orders` | Admin Service | Order management |
| `PATCH` | `/admin/orders/{id}` | Admin Service | Update order status |
| `GET` | `/admin/products` | Catalog Service | Product management |

---

## Rate Limiting

### Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `RATE_LIMIT_RPS` | 100 | Requests per second |
| `RATE_LIMIT_BURST` | 200 | Maximum burst size |
| `RATE_LIMIT_WINDOW` | 60s | Rate limit window |

### Rate Limit Headers

All responses include rate limit headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1722686460
Retry-After: 30         # Only on 429 responses
```

### Rate Limit by Route

| Route Group | RPS Limit | Burst | Description |
|-------------|-----------|-------|-------------|
| Public (products, categories) | 200 | 400 | High throughput for browsing |
| Auth (login, register) | 10 | 20 | Strict to prevent brute force |
| Authenticated (cart, orders) | 50 | 100 | Moderate for user operations |
| Admin | 30 | 60 | Restricted for management |
| Search | 100 | 200 | Moderate for search queries |

### Rate Limit Response

**429 Too Many Requests**

```json
{
  "detail": "Rate limit exceeded. Try again in 30 seconds.",
  "retry_after": 30
}
```

---

## CORS Configuration

### Default CORS Settings

| Setting | Default Value |
|---------|--------------|
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:8080` |
| `CORS_ALLOWED_METHODS` | `GET,POST,PUT,PATCH,DELETE,OPTIONS` |
| `CORS_ALLOWED_HEADERS` | `Content-Type,Authorization,X-Request-ID` |
| `CORS_MAX_AGE` | 86400 (24 hours) |
| `CORS_ALLOW_CREDENTIALS` | `true` |

### Production CORS

For production, set `CORS_ALLOWED_ORIGINS` to specific domains:

```bash
CORS_ALLOWED_ORIGINS=https://app.marketplace.com,https://admin.marketplace.com
```

### Preflight Request Handling

The gateway automatically handles `OPTIONS` preflight requests:

```
OPTIONS /api/resource
    → 204 No Content (with CORS headers)
```

---

## Request/Response Transformation

### Request Transformation

| Transformation | Description |
|---------------|-------------|
| **Request ID** | Generated if not present; propagated via `X-Request-ID` |
| **Auth Header** | Bearer token extracted and validated |
| **User Context** | JWT payload injected into request state |
| **Content-Type** | Normalized to `application/json` |
| **Body Size** | Enforced 10 MB limit |

### Response Transformation

| Transformation | Description |
|---------------|-------------|
| **Security Headers** | HSTS, CSP, X-Frame-Options, etc. |
| **Request ID** | Propagated to response header |
| **Error Normalization** | Service errors normalized to consistent format |
| **Timing** | `X-Response-Time` header added |

### Error Response Format

All errors follow a consistent format:

```json
{
  "detail": "Error description",
  "request_id": "req_abc123",
  "timestamp": "2026-08-03T10:00:00Z"
}
```

---

## Circuit Breaker

### Overview

The gateway implements a circuit breaker pattern to prevent cascading failures when backend services are unavailable.

### Circuit Breaker States

```
          ┌─────────┐
          │  CLOSED  │ ◄── Normal operation
          └────┬─────┘
               │ failures > threshold
               ▼
          ┌─────────┐
          │ OPEN     │ ◄── Failures, reject immediately
          └────┬─────┘
               │ timeout elapsed
               ▼
          ┌─────────┐
          │ HALF-OPEN │ ◄── Test with limited requests
          └────┬─────┘
               │ success
               ▼
          ┌─────────┐
          │  CLOSED  │ ◄── Recovery
          └─────────┘
```

### Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `failure_threshold` | 5 | Failures before opening circuit |
| `recovery_timeout` | 30s | Time before half-open test |
| `half_open_max_requests` | 3 | Test requests in half-open state |
| `half_open_success_threshold` | 2 | Successes needed to close |

### Circuit Breaker Response

**503 Service Unavailable** (circuit open):

```json
{
  "detail": "Service temporarily unavailable. Please try again later.",
  "service": "order-service",
  "retry_after": 30
}
```

---

## Security Headers

The gateway applies the following security headers to all responses:

| Header | Value | Purpose |
|--------|-------|---------|
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` | Enforce HTTPS |
| `Content-Security-Policy` | `default-src 'self'; ...` | Prevent XSS |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | XSS filter |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer info |
| `Permissions-Policy` | `geolocation=(), camera=(), ...` | Restrict browser features |
| `Cache-Control` | `no-store, no-cache, must-revalidate` | Prevent caching |

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_PORT` | 8080 | HTTP port |
| `AUTH_SERVICE_HOST` | auth-service | Auth service hostname |
| `AUTH_SERVICE_PORT` | 50052 | Auth service gRPC port |
| `BFF_SERVICE_HOST` | bff-service | BFF service hostname |
| `BFF_SERVICE_PORT` | 8085 | BFF service HTTP port |
| `LOG_LEVEL` | info | Log level |
| `MAX_REQUEST_BODY_SIZE` | 10485760 | Max body size in bytes |
| `REQUEST_TIMEOUT` | 30 | Request timeout in seconds |
| `ADMIN_IP_WHITELIST` | 127.0.0.1,::1 | Admin endpoint IP whitelist |
| `CORS_ALLOWED_ORIGINS` | localhost origins | CORS allowed origins |
| `RATE_LIMIT_RPS` | 100 | Rate limit requests per second |
| `RATE_LIMIT_BURST` | 200 | Rate limit burst size |

### Docker Compose

```yaml
gateway:
  build:
    context: ./12-gateway
    dockerfile: Dockerfile
  container_name: marketplace-gateway
  ports:
    - "8080:8080"
  environment:
    - SERVER_PORT=8080
    - AUTH_SERVICE_HOST=auth-service
    - AUTH_SERVICE_PORT=50052
    - LOG_LEVEL=info
  depends_on:
    auth-service:
      condition: service_healthy
  networks:
    - marketplace
```

---

## Related Documentation

- [Authentication](authentication.md) — JWT and API key auth
- [Services Overview](services.md) — Service architecture
- [Deployment Guide](deployment.md) — Production gateway setup
