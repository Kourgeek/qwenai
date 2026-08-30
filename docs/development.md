# Development Guide

Guide for setting up the HyperScale Marketplace for local development, testing, and contributing.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
- [Running Individual Services](#running-individual-services)
- [Testing](#testing)
- [Code Style](#code-style)
- [Debugging](#debugging)
- [CI/CD](#cicd)

---

## Prerequisites

| Tool | Minimum Version | Purpose |
|------|----------------|---------|
| Docker | 24.0 | Containerization |
| Docker Compose | 2.20 | Orchestration |
| Python | 3.12 | Runtime for all services |
| Make | 4.0+ | Build automation (optional) |
| git | 2.40+ | Version control |

### Python Dependencies

Each service has its own `requirements.txt` or `pyproject.toml`. Common dependencies:

```
fastapi>=0.104.0
uvicorn>=0.24.0
sqlalchemy>=2.0.0
asyncpg>=0.29.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
grpcio>=1.59.0
grpcio-tools>=1.59.0
kafka-python>=2.0.2
redis>=5.0.0
stripe>=7.0.0
httpx>=0.25.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
ruff>=0.1.0
```

---

## Local Setup

### 1. Clone and Configure

```bash
# Clone the repository
cd migration_plan

# Copy environment variables
cp .env.example .env

# Edit .env with your local settings
# At minimum, set:
#   JWT_SECRET=<strong-random-string>
#   DB_PASSWORD=<your-password>
```

### 2. Start Infrastructure

```bash
# Start infrastructure services only
docker compose --profile infra up -d

# Wait for services to be healthy
docker compose --profile infra ps

# Expected output:
# marketplace-postgres       healthy
# marketplace-redis          healthy
# marketplace-elasticsearch  healthy
# marketplace-kafka          healthy
# marketplace-zookeeper      healthy
```

### 3. Start Application Services

```bash
# Start all application services
docker compose --profile services up -d

# Verify all services are running
docker compose --profile all ps
```

### 4. Run Database Migrations

```bash
# Run migrations for all services
make migrate

# Run migrations for a specific service
make migrate service=auth-service
```

### 5. Verify Everything

```bash
# Check health of all services
make health

# View logs
make logs
```

---

## Running Individual Services

### Running a Service Standalone

```bash
# Navigate to the service directory
cd 01-auth-service

# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn src.main:app --host 0.0.0.0 --port 50052 --reload

# Or with Python directly
python -m uvicorn src.main:app --host 0.0.0.0 --port 50052 --reload
```

### Service-Specific Commands

| Service | Command | Port |
|---------|---------|------|
| auth-service | `uvicorn src.main:app --port 50052` | 50052 |
| catalog-service | `uvicorn src.main:app --port 8080` | 8080 |
| cart-service | `uvicorn src.main:app --port 8081` | 8081 |
| order-service | `uvicorn src.main:app --port 8085` | 8085 |
| payment-service | `uvicorn src.main:app --port 50056` | 50056 |
| notification-service | `uvicorn src.main:app --port 8086` | 8086 |
| search-service | `uvicorn src.main:app --port 8083` | 8083 |
| seller-service | `uvicorn src.main:app --port 8085` | 8085 |
| admin-service | `uvicorn src.main:app --port 8085` | 8085 |
| bff-service | `uvicorn src.main:app --port 8085` | 8085 |
| gateway | `uvicorn src.main:app --port 8080` | 8080 |

### Running with Docker (Single Service)

```bash
# Build and run a specific service
docker compose --profile services up -d --build auth-service

# Or build from source directory
cd 01-auth-service
docker build -t marketplace-auth-service .
docker run -p 50052:50052 --network marketplace marketplace-auth-service
```

---

## Testing

### Run All Tests

```bash
make test
```

### Run Tests for a Specific Service

```bash
make test service=auth-service
make test service=catalog-service
make test service=order-service
```

### Run Tests Manually

```bash
cd 01-auth-service
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test file
python -m pytest tests/test_auth_service.py -v

# Run specific test
python -m pytest tests/test_auth_service.py::test_login_success -v
```

### Test Structure

```
01-auth-service/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── test_auth_service.py     # Auth service tests
│   ├── test_jwt.py              # JWT token tests
│   └── test_password_service.py # Password hashing tests
├── src/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── auth/
│   ├── services/
│   ├── repositories/
│   ├── models/
│   └── middleware/
└── requirements.txt
```

### Test Fixtures (conftest.py)

Common fixtures provided:

| Fixture | Description |
|---------|-------------|
| `db_session` | Async database session (mocked) |
| `redis_client` | Redis client (mocked) |
| `auth_client` | Test HTTP client |
| `test_user` | Pre-created test user |
| `test_token` | Pre-generated JWT token |

### Testing Infrastructure

```bash
# Start test infrastructure
docker compose --profile dev up -d

# Run tests against test infrastructure
make test service=auth-service

# Stop test infrastructure
docker compose --profile dev down
```

---

## Code Style

### Linting

```bash
# Lint all services
make lint

# Lint a specific service
make lint service=auth-service
```

### Code Formatting

The project uses **Ruff** for linting and formatting:

```bash
# Auto-format all services
ruff format .

# Check formatting
ruff format --check .

# Lint all services
ruff check .

# Lint a specific service
cd 01-auth-service && ruff check src/ tests/
```

### Style Guide

| Rule | Standard |
|------|----------|
| **Line length** | 120 characters |
| **Indentation** | 4 spaces |
| **Quotes** | Single quotes (Ruff default) |
| **Imports** | Sorted by Ruff (`isort`) |
| **Type hints** | Required for all function signatures |
| **Docstrings** | Google style for public APIs |
| **Naming** | `snake_case` for functions/variables, `PascalCase` for classes |

### Pre-commit Hooks

Recommended pre-commit configuration (`.pre-commit-config.yaml`):

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.13.0
    hooks:
      - id: isort
```

---

## Debugging

### View Service Logs

```bash
# All logs
make logs

# Specific service
make logs service=gateway
make logs service=auth-service

# Follow logs in real-time
make logs service=order-service
```

### Open Shell in Container

```bash
make bash service=gateway
make bash service=auth-service
```

### Debug with Docker Compose

```bash
# Run with debug logging
docker compose --profile services up -d
docker compose --profile services logs -f

# Check specific service logs with tail
docker compose --profile services logs --tail=100 gateway
```

### Debugging Tips

| Issue | Solution |
|-------|----------|
| Service won't start | Check `docker compose logs <service>` |
| DB connection fails | Verify `DB_HOST=postgres` and PostgreSQL is healthy |
| Redis errors | Check `REDIS_HOST=redis` and Redis health |
| gRPC connection refused | Verify gRPC port mapping in docker-compose |
| Kafka errors | Check Zookeeper is healthy first |
| Elasticsearch errors | Check ES health at `http://localhost:9200` |
| CORS errors | Check `CORS_ALLOWED_ORIGINS` in `.env` |

### Debugging gRPC

```bash
# Generate proto files
grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. --pyi_out=. \
  proto/auth/v1/auth.proto

# Test gRPC service
grpcurl -plaintext localhost:50051 auth.v1.AuthService/Login \
  -d '{"email": "test@example.com", "password": "password"}'
```

---

## CI/CD

### Pipeline Overview

```
Push to main
     │
     ▼
┌─────────────────┐
│  1. Lint & Format│
│     (Ruff)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. Run Tests    │
│     (pytest)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  3. Build Images │
│     (Docker)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  4. Push to      │
│     Registry     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  5. Deploy to    │
│     Staging      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  6. Integration  │
│     Tests        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  7. Deploy to    │
│     Production   │
└─────────────────┘
```

### GitHub Actions (`.github/workflows/ci.yml`)

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install ruff
      - run: ruff check .
      - run: ruff format --check .

  test:
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --cov=src

  build:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: marketplace-service:latest
```

### Makefile Commands Summary

| Command | Description |
|---------|-------------|
| `make up` | Start all services |
| `make down` | Stop all services |
| `make restart` | Restart all services |
| `make logs [service=X]` | View logs |
| `make test [service=X]` | Run tests |
| `make lint [service=X]` | Run linter |
| `make migrate [service=X]` | Run migrations |
| `make build [service=X]` | Build service image |
| `make clean` | Remove containers, volumes, images |
| `make health` | Check service health |
| `make docs` | Generate API docs |
| `make bash service=X` | Open bash in container |

---

## Related Documentation

- [Main README](../README.md) — Project overview
- [Deployment Guide](deployment.md) — Production deployment
- [Monitoring](monitoring.md) — Observability setup
- [Gateway Documentation](gateway.md) — API gateway details
