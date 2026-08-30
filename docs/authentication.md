# Authentication

Authentication in HyperScale Marketplace uses a combination of JWT (JSON Web Tokens) for stateless authentication, API keys for service-to-service auth, and OAuth2 for third-party integrations.

---

## Table of Contents

- [JWT Authentication Flow](#jwt-authentication-flow)
- [API Key Authentication](#api-key-authentication)
- [OAuth2 Flow](#oauth2-flow)
- [Token Refresh](#token-refresh)
- [Security Best Practices](#security-best-practices)

---

## JWT Authentication Flow

### Overview

The Auth Service issues JWT tokens upon successful login. Tokens are used for subsequent authenticated requests across the platform.

### Flow Diagram

```
Client                          Auth Service                    Other Services
  |                                   |                                |
  |  POST /auth/login                 |                                |
  |  {email, password}                |                                |
  |---------------------------------->|                                |
  |                                   |  Verify credentials            |
  |                                   |  (PostgreSQL)                  |
  |                                   |                                |
  |  {access_token,                  |                                |
  |   refresh_token,                 |                                |
  |   expires_at}                    |                                |
  |<----------------------------------|                                |
  |                                   |                                |
  |  Authorization: Bearer            |                                |
  |  <access_token>                   |                                |
  |---------------------------------->|                                |
  |                                   |  Validate JWT                  |
  |                                   |  (signature + expiry)          |
  |                                   |                                |
  |  {response data}                 |  Forward to backend            |
  |<----------------------------------|<-------------------------------|
```

### Login Endpoint

**POST** `/auth/login`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User email address |
| password | string | Yes | User password |

**Response (200 OK)**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "access_expires_at": "2026-08-03T12:00:00Z",
  "refresh_expires_at": "2026-08-04T12:00:00Z",
  "user_id": "usr_abc123",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

### Register Endpoint

**POST** `/auth/register`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User email address |
| password | string | Yes | Password (min 8 chars) |
| first_name | string | No | User first name |
| last_name | string | No | User last name |

**Response (201 Created)**

```json
{
  "id": "usr_abc123",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "created_at": "2026-08-03T10:00:00Z"
}
```

### gRPC Authentication

The Auth Service also exposes gRPC endpoints for service-to-service authentication:

```protobuf
service AuthService {
  rpc Register(RegisterRequest) returns (RegisterResponse);
  rpc Login(LoginRequest) returns (LoginResponse);
  rpc Refresh(RefreshRequest) returns (RefreshResponse);
  rpc Logout(LogoutRequest) returns (LogoutResponse);
  rpc ForgotPassword(ForgotPasswordRequest) returns (ForgotPasswordResponse);
}
```

**gRPC Port:** `50051` (host-mapped)

### Token Structure

**Access Token (JWT):**

```
Header:  {"alg": "HS256", "typ": "JWT"}
Payload: {
  "sub": "usr_abc123",
  "email": "user@example.com",
  "role": "user",
  "iat": 1722686400,
  "exp": 1722690000,
  "iss": "auth-service"
}
```

| Claim | Description |
|-------|-------------|
| `sub` | User ID |
| `email` | User email |
| `role` | User role (`user`, `seller`, `admin`) |
| `iat` | Issued at (Unix timestamp) |
| `exp` | Expiration (Unix timestamp) |
| `iss` | Issuer (`auth-service`) |

---

## API Key Authentication

### Overview

API keys are used for:

- **Seller Service:** Seller API access
- **Service-to-Service:** Internal microservice communication
- **Third-party Integrations:** External partner access

### Key Format

```
hs_live_<random_string>    # Production keys
hs_test_<random_string>    # Test keys
```

### Usage

Include the API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: hs_live_abc123" \
     https://api.marketplace.local/seller/products
```

### Key Management

- Keys are stored hashed (SHA-256) in the database
- Keys can be rotated without service interruption
- Expired keys are automatically rejected
- Admin dashboard for key management

---

## OAuth2 Flow

### Overview

OAuth2 is supported for third-party authentication and authorization:

- **Google Sign-In**
- **Apple Sign-In**
- **Yandex (for Russian market)**

### Authorization Code Flow

```
Client                    Marketplace                    Identity Provider
  |                             |                                |
  |  Authorization Request      |                                |
  |  (redirect to /oauth/...)   |                                |
  |-------------------------------------------------------------->|
  |                             |                                |
  |  User authenticates         |                                |
  |  and grants consent         |                                |
  |<-------------------------------------------------------------|
  |                             |                                |
  |  Authorization Code         |                                |
  |  (redirect back)            |                                |
  |-------------------------------------------------------------->|
  |                             |  Token Request                 |
  |                             |-------------------------------->|
  |                             |                                |
  |                             |  Access + Refresh Tokens       |
  |                             |<-------------------------------|
  |                             |                                |
  |  Store tokens               |                                |
  |<----------------------------|                                |
```

### Token Endpoint

**POST** `/oauth/token`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| grant_type | string | Yes | `authorization_code` or `refresh_token` |
| code | string | Conditional | Authorization code |
| redirect_uri | string | Conditional | Registered redirect URI |
| client_id | string | Yes | OAuth client ID |
| client_secret | string | Yes | OAuth client secret |
| refresh_token | string | Conditional | Refresh token |

---

## Token Refresh

### Overview

When the access token expires, use the refresh token to obtain a new access token without requiring re-authentication.

### Refresh Flow

**POST** `/auth/refresh`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| refresh_token | string | Yes | Valid refresh token |

**Response (200 OK)**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "access_expires_at": "2026-08-03T13:00:00Z",
  "refresh_expires_at": "2026-08-04T13:00:00Z"
}
```

### Token Lifecycle

```
User Login
    │
    ├── Access Token (1 hour) ────────────────┐
    │   │                                     │
    │   │ Expires                             │
    │   │                                     │
    │   ▼                                     ▼
    │  Refresh Token (7 days) ── Expires ──►  Logout Required
    │       │
    │       │ Refresh (before expiry)
    │       │
    │       ▼
    │  New Access Token (1 hour)
    │  New Refresh Token (7 days from now)
    │
    ▼
Logout (invalidates refresh token in Redis)
```

### Refresh Token Rotation

Each refresh rotates the refresh token:

1. Old refresh token is invalidated (added to Redis blacklist)
2. New refresh token is issued with extended expiry
3. Reuse of an old refresh token is rejected

---

## Security Best Practices

### Token Security

| Practice | Description |
|----------|-------------|
| **Short-lived access tokens** | 1 hour default (configurable via `JWT_EXPIRY`) |
| **Secure refresh tokens** | 7 days with rotation |
| **JWT signing** | HS256 algorithm with strong secret |
| **Token revocation** | Blacklisted in Redis on logout |
| **HTTPS only** | Tokens transmitted over TLS in production |

### Password Security

| Practice | Description |
|----------|-------------|
| **Hashing** | bcrypt with cost factor 12 |
| **Minimum length** | 8 characters |
| **Rate limiting** | 5 login attempts per minute per IP |
| **Account lockout** | After 10 failed attempts (15 min cooldown) |
| **Password reset** | Time-limited token (1 hour) via email |

### API Key Security

| Practice | Description |
|----------|-------------|
| **Storage** | SHA-256 hashed in database |
| **Transmission** | Via `X-API-Key` header over TLS |
| **Rotation** | Manual or automated key rotation |
| **Scoping** | Keys scoped to specific resources/permissions |

### General Security

| Practice | Description |
|----------|-------------|
| **CORS** | Configurable per environment via `CORS_ALLOWED_ORIGINS` |
| **Rate limiting** | Gateway-level: 100 req/s default (configurable) |
| **Request size limit** | 10 MB max body size |
| **Security headers** | HSTS, CSP, X-Frame-Options, etc. |
| **Audit logging** | All auth events logged with request ID |
| **Secrets management** | Use Vault/AWS Secrets Manager in production |

### Environment Variables for Auth

```bash
# JWT Configuration
JWT_SECRET=change-me-to-a-strong-random-string-in-production
JWT_EXPIRY=3600
JWT_ISSUER=auth-service
JWT_ALGORITHM=HS256

# Password hashing
BCRYPT_ROUNDS=12

# Rate limiting
RATE_LIMIT_RPS=100
RATE_LIMIT_BURST=200
```

---

## Error Responses

| Status | Description |
|--------|-------------|
| `400` | Invalid request body or missing fields |
| `401` | Invalid credentials or expired token |
| `403` | Insufficient permissions |
| `409` | Email already registered |
| `423` | Account locked (too many failed attempts) |
| `429` | Rate limit exceeded |
| `500` | Internal server error |

---

## Related Documentation

- [Gateway Documentation](gateway.md) — Rate limiting and CORS configuration
- [gRPC API Reference](grpc-api.md) — Auth service gRPC endpoints
- [Deployment Guide](deployment.md) — Production security setup
