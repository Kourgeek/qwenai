# Auth Service API Documentation

Authentication service providing user registration, login, token management, and password recovery.

---

## Table of Contents

- [Overview](#overview)
- [Protocol](#protocol)
- [Endpoints](#endpoints)
- [gRPC API](#grpc-api)
- [Error Codes](#error-codes)
- [Examples](#examples)

---

## Overview

The Auth Service handles all authentication and authorization operations for the HyperScale Marketplace. It manages user registration, login, JWT token issuance and refresh, logout (token blacklisting), and password recovery.

**Base URL (HTTP):** `http://localhost:8080/auth` (via Gateway)
**gRPC Target:** `localhost:50051` (host-mapped)

---

## Protocol

| Protocol | Port | Description |
|----------|------|-------------|
| HTTP (REST) | 8080 (via Gateway) | Public-facing authentication |
| gRPC | 50051 (host-mapped) | Service-to-service auth |

### Authentication Methods

1. **JWT Bearer Token** — For authenticated API requests
2. **API Key** — For service-to-service communication
3. **gRPC metadata** — For internal service auth

---

## Endpoints

### Register

**POST** `/auth/register`

Register a new user account.

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User email address (must be unique) |
| password | string | Yes | Password (min 8 characters) |
| first_name | string | No | User first name |
| last_name | string | No | User last name |

#### Example Request

```bash
curl -X POST http://localhost:8080/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

#### Response (201 Created)

```json
{
  "id": "usr_abc123",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "created_at": "2026-08-03T10:00:00Z"
}
```

#### Error Responses

| Status | Detail |
|--------|--------|
| 400 | `Email and password are required` |
| 409 | `Email already registered` |
| 502 | `Auth service unavailable` |

---

### Login

**POST** `/auth/login`

Authenticate a user and receive JWT tokens.

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User email address |
| password | string | Yes | User password |

#### Example Request

```bash
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

#### Response (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access_expires_at": "2026-08-03T11:00:00Z",
  "refresh_expires_at": "2026-08-04T10:00:00Z",
  "user_id": "usr_abc123",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### Error Responses

| Status | Detail |
|--------|--------|
| 400 | `Email and password are required` |
| 401 | `Invalid credentials` |
| 423 | `Account locked` |
| 502 | `Auth service unavailable` |

---

### Token Refresh

**POST** `/auth/refresh`

Obtain a new access token using a valid refresh token.

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| refresh_token | string | Yes | Valid refresh token |

#### Example Request

```bash
curl -X POST http://localhost:8080/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

#### Response (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access_expires_at": "2026-08-03T12:00:00Z",
  "refresh_expires_at": "2026-08-04T12:00:00Z"
}
```

#### Error Responses

| Status | Detail |
|--------|--------|
| 400 | `Refresh token is required` |
| 401 | `Invalid or expired refresh token` |
| 502 | `Auth service unavailable` |

---

### Logout

**POST** `/auth/logout`

Invalidate the current refresh token (blacklist).

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| refresh_token | string | Yes | Refresh token to invalidate |

#### Example Request

```bash
curl -X POST http://localhost:8080/auth/logout \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

#### Response (200 OK)

```json
{
  "success": true,
  "message": "Token invalidated successfully"
}
```

---

### Forgot Password

**POST** `/auth/forgot-password`

Send a password reset link to the user's email.

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User email address |

#### Example Request

```bash
curl -X POST http://localhost:8080/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

#### Response (200 OK)

```json
{
  "success": true,
  "message": "Password reset email sent"
}
```

---

## gRPC API

### Service Definition

```protobuf
service AuthService {
  // Register creates a new user account.
  rpc Register(RegisterRequest) returns (RegisterResponse);
  
  // Login authenticates a user and returns JWT tokens.
  rpc Login(LoginRequest) returns (LoginResponse);
  
  // Refresh issues a new access token using a valid refresh token.
  rpc Refresh(RefreshRequest) returns (RefreshResponse);
  
  // Logout invalidates the refresh token (blacklisting).
  rpc Logout(LogoutRequest) returns (LogoutResponse);
  
  // ForgotPassword sends a password reset link to the user's email.
  rpc ForgotPassword(ForgotPasswordRequest) returns (ForgotPasswordResponse);
}
```

### Message Types

#### RegisterRequest

```protobuf
message RegisterRequest {
  string email = 1;
  string password = 2;
  string first_name = 3;
  string last_name = 4;
}
```

#### RegisterResponse

```protobuf
message RegisterResponse {
  string id = 1;
  string email = 2;
  string first_name = 3;
  string last_name = 4;
  google.protobuf.Timestamp created_at = 5;
}
```

#### LoginRequest

```protobuf
message LoginRequest {
  string email = 1;
  string password = 2;
}
```

#### LoginResponse

```protobuf
message LoginResponse {
  string access_token = 1;
  string refresh_token = 2;
  google.protobuf.Timestamp access_expires_at = 3;
  google.protobuf.Timestamp refresh_expires_at = 4;
  string user_id = 5;
  string email = 6;
  string first_name = 7;
  string last_name = 8;
}
```

#### RefreshRequest

```protobuf
message RefreshRequest {
  string refresh_token = 1;
}
```

#### RefreshResponse

```protobuf
message RefreshResponse {
  string access_token = 1;
  string refresh_token = 2;
  google.protobuf.Timestamp access_expires_at = 3;
  google.protobuf.Timestamp refresh_expires_at = 4;
}
```

#### LogoutRequest

```protobuf
message LogoutRequest {
  string refresh_token = 1;
}
```

#### LogoutResponse

```protobuf
message LogoutResponse {
  bool success = 1;
  string message = 2;
}
```

#### ForgotPasswordRequest

```protobuf
message ForgotPasswordRequest {
  string email = 1;
}
```

#### ForgotPasswordResponse

```protobuf
message ForgotPasswordResponse {
  bool success = 1;
  string message = 2;
}
```

### gRPC Examples

#### Python

```python
import grpc
import auth_pb2
import auth_pb2_grpc

channel = grpc.insecure_channel('localhost:50051')
stub = auth_pb2_grpc.AuthServiceStub(channel)

# Login
response = stub.Login(
    auth_pb2.LoginRequest(
        email="user@example.com",
        password="SecurePass123!"
    )
)
print(f"Access token: {response.access_token}")
print(f"Refresh token: {response.refresh_token}")
```

#### JavaScript

```javascript
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');

const packageDef = protoLoader.loadSync('proto/auth/v1/auth.proto');
const authProto = grpc.loadPackageDefinition(packageDef);

const client = new authProto.auth.v1.AuthService(
  'localhost:50051',
  grpc.credentials.createInsecure()
);

client.Login(
  { email: 'user@example.com', password: 'SecurePass123!' },
  (err, response) => {
    if (err) {
      console.error('Login failed:', err);
      return;
    }
    console.log('Access token:', response.access_token);
    console.log('Refresh token:', response.refresh_token);
  }
);
```

---

## Error Codes

| gRPC Status | HTTP Status | Description |
|-------------|-------------|-------------|
| `INVALID_ARGUMENT` | 400 | Invalid request parameters |
| `UNAUTHENTICATED` | 401 | Invalid credentials |
| `ALREADY_EXISTS` | 409 | Email already registered |
| `RESOURCE_EXHAUSTED` | 423 | Account locked |
| `UNAVAILABLE` | 503 | Service unavailable |
| `INTERNAL` | 500 | Internal server error |

---

## Examples

### Full Registration Flow

```bash
# 1. Register
curl -X POST http://localhost:8080/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}'

# 2. Login
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}'

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIs...",
#   "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
#   "user_id": "usr_abc123",
#   ...
# }

# 3. Use token for authenticated requests
curl -X GET http://localhost:8089/bff/profile \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Token Refresh Flow

```bash
# 1. Get initial tokens
TOKENS=$(curl -s -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}')

# 2. Refresh when expired
curl -X POST http://localhost:8080/auth/refresh \
  -H "Content-Type: application/json" \
  -d "$(echo $TOKENS | jq '{refresh_token: .refresh_token}')"
```

---

## Related Documentation

- [Authentication Overview](authentication.md)
- [Gateway Documentation](gateway.md)
- [gRPC API Reference](grpc-api.md)
