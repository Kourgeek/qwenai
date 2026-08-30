# Cart Service — HyperScale Marketplace (Phase 5)

## Quick Start

```bash
# 1. Install dependencies
pip install -e ".[dev]"

# 2. Copy and configure environment
cp .env.example .env
# Edit .env with your actual Redis / DB / service addresses

# 3. Run the service
uvicorn src.main:app --host 0.0.0.0 --port 8081 --reload

# 4. Run tests
pytest tests/ -v
```

## Architecture

```
┌──────────────┐     gRPC      ┌──────────────┐
│   Client     │──────────────▶│ Auth Service  │
│ (HTTP/gRPC)  │◀──────────────│ (verify JWT)  │
└──────┬───────┘              └──────────────┘
       │
       │  gRPC
       ▼
┌──────────────┐     gRPC      ┌──────────────┐
│ Cart Service │──────────────▶│ Catalog Svc   │
│  (FastAPI    │               │ (get product) │
│   + gRPC)    │◀──────────────└──────────────┘
└──────┬───────┘
       │
       ▼
  ┌─────────┐
  │  Redis   │   JSON cart data with TTL
  │ (db=3)   │
  └─────────┘
```

## API Endpoints

| Method | Path                      | Description            |
|--------|---------------------------|------------------------|
| GET    | `/api/v1/cart`            | Get current cart       |
| POST   | `/api/v1/cart/items`      | Add item to cart       |
| PUT    | `/api/v1/cart/items/{id}` | Update item quantity   |
| DELETE | `/api/v1/cart/items/{id}` | Remove item from cart  |
| POST   | `/api/v1/cart/clear`      | Clear entire cart      |
| POST   | `/api/v1/cart/save-for-later` | Save item for later |
| POST   | `/api/v1/cart/move-to-cart`   | Move item back to cart |

**Authentication:** Pass `x-user-id` header (JWT subject).

## gRPC Endpoints

All RPCs defined in `cart.proto` — see `src/grpc_server/cart_pb2_service.py`.

## Docker

```bash
docker build -t cart-service:latest .
docker run -p 8081:8081 -p 50050:50050 --env-file .env cart-service:latest
```

## Project Structure

```
04-cart-service/
├── pyproject.toml          # Dependencies & build config
├── Dockerfile              # Container definition
├── .env.example            # Environment template
├── src/
│   ├── config.py           # Pydantic settings
│   ├── main.py             # FastAPI app + gRPC lifecycle
│   ├── redis_client.py     # Async Redis client
│   ├── api/
│   │   └── cart.py         # HTTP router
│   ├── grpc_client/
│   │   ├── auth_client.py  # Auth gRPC client
│   │   ├── catalog_client.py # Catalog gRPC client
│   │   └── cart_pb2.py     # Proto stubs (shim)
│   ├── grpc_server/
│   │   └── cart_pb2_service.py  # gRPC servicer
│   └── services/
│       └── cart_service.py # Business logic
└── tests/
    ├── conftest.py         # Shared fixtures
    └── test_cart_service.py
```
