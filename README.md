# HyperScale Marketplace

> A scalable, microservices-based e-commerce marketplace platform with Python (FastAPI) services, gRPC inter-service communication, and Kafka event streaming.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Service Table](#service-table)
- [Infrastructure](#infrastructure)
- [API Documentation](#api-documentation)
- [Development Guide](#development-guide)
- [Deployment Guide](#deployment-guide)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Architecture Overview

```
                                    ┌──────────────────┐
                                    │   Web / Mobile   │
                                    │     Clients      │
                                    └────────┬─────────┘
                                             │
                                             ▼
                          ┌─────────────────────────────────┐
                          │        API Gateway              │
                          │        (port 8080)              │
                          │  Auth · Rate Limit · CORS       │
                          └─────────────────────────────────┘
                                             │
                   ┌─────────────────────────┼─────────────────────────┐
                   │                         │                         │
                   ▼                         ▼                         ▼
          ┌───────────────┐       ┌──────────────────┐      ┌───────────────┐
          │  Auth Service  │       │   BFF Service    │      │  Admin Service│
          │  (gRPC 50052)  │       │   (port 8089)    │      │  (port 8088)  │
          └───────┬───────┘       └────────┬─────────┘      └───────────────┘
                  │                         │                         │
                  ▼                         ▼                         │
          ┌───────────────┐       ┌──────────────────┐              │
          │  User Service  │       │  Catalog Service  │◄─────────────┘
          │  (gRPC 50053)  │       │  (HTTP 8084 /     │
          └───────┬───────┘       │   gRPC 50053)      │
                  │               └────────┬───────────┘
                  │                        │
                  ▼                        ▼
          ┌───────────────┐       ┌──────────────────┐
          │  Cart Service  │       │  Search Service   │
          │  (HTTP 8081 /  │       │  (HTTP 8087 /     │
          │   gRPC 50054)  │       │   gRPC 50058)     │
          └───────┬───────┘       └──────────────────┘
                  │
                  ▼
          ┌───────────────┐       ┌──────────────────┐
          │  Order Service │       │  Payment Service  │
          │  (HTTP 8085 /  │       │  (HTTP 8082 /     │
          │   gRPC 50055)  │       │   gRPC 50056)     │
          └───────┬───────┘       └────────┬───────────┘
                  │                         │
                  ▼                         ▼
          ┌──────────────────────────────────────────┐
          │           Kafka (port 9092)              │
          │  order.created · order.status_changed     │
          │  payment.completed · payment.failed       │
          └──────────────────────────────────────────┘
                  │
                  ▼
          ┌──────────────────────────────────────────┐
          │  Notification Service                    │
          │  (HTTP 8086 / gRPC 50057)                │
          │  Email · Push · SMS                      │
          └──────────────────────────────────────────┘
                  │
          ┌───────┴──────────┐
          ▼                  ▼
   ┌───────────┐     ┌────────────┐
   │  SMTP /   │     │ Firebase / │
   │  Mailhog  │     │  Twilio    │
   └───────────┘     └────────────┘

  Databases (PostgreSQL 16):
  ┌──────────────────────────────────────────────────────────────┐
  │  auth_db  │ user_db  │ catalog_db  │ cart_db  │ order_db   │
  │  payment_db │ notification_db │ search_db │ seller_db │ admin_db │
  └──────────────────────────────────────────────────────────────┘

  Caching & Search:
  ┌───────────┐  ┌──────────────┐  ┌──────────────┐
  │  Redis 7  │  │ Elasticsearch│  │   Kibana     │
  │  (6379)   │  │  (9200)      │  │  (5601)      │
  └───────────┘  └──────────────┘  └──────────────┘

  Monitoring:
  ┌───────────┐  ┌───────────┐
  │ Prometheus│  │  Grafana  │
  │ (9090)    │  │ (3000)    │
  └───────────┘  └───────────┘
```

---

## Tech Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Language** | Python | 3.12 | All services |
| **Web Framework** | FastAPI | latest | HTTP API |
| **RPC** | gRPC + protobuf | 3 | Inter-service communication |
| **Database** | PostgreSQL | 16 | Persistent storage (per-service) |
| **Cache** | Redis | 7 | Caching, sessions, rate limiting |
| **Search** | Elasticsearch | 8.12 | Product search, indexing |
| **Message Broker** | Apache Kafka | 3.5 | Event streaming, async processing |
| **ORM** | SQLAlchemy | 2.x (async) | Database access |
| **Migrations** | Alembic | latest | Schema migrations |
| **Validation** | Pydantic | 2.x | Request/response validation |
| **API Docs** | Swagger / ReDoc | — | Auto-generated API docs |
| **Monitoring** | Prometheus + Grafana | 2.48 / 10.1 | Metrics, dashboards, alerting |
| **Logging** | Python logging (JSON) | — | Structured logging |
| **Container** | Docker + Docker Compose | — | Local dev & deployment |
| **Testing** | pytest + pytest-cov | latest | Unit & integration tests |
| **Linting** | Ruff | latest | Code quality |

---

## Quick Start

### Prerequisites

- Docker 24+ and Docker Compose v2+
- Python 3.12 (for local development)
- Make (optional, for convenience commands)

### Start All Services

```bash
# 1. Copy environment variables
cp .env.example .env

# 2. Start infrastructure (PostgreSQL, Redis, Elasticsearch, Kafka, etc.)
docker compose --profile infra up -d

# 3. Wait for infrastructure to be healthy
docker compose --profile infra ps

# 4. Start application services
docker compose --profile services up -d

# 5. Start monitoring stack
docker compose --profile monitoring up -d

# Or start everything at once:
docker compose --profile all up -d
```

### Verify Services

```bash
# Check health of all services
make health

# View logs
make logs

# View logs for a specific service
make logs service=gateway

# Check running containers
docker compose --profile all ps
```

### Stop All Services

```bash
docker compose --profile all down
```

### Clean Up

```bash
make clean
# Removes containers, volumes, and dangling images
```

---

## Service Table

| Service | HTTP Port | gRPC Port | Description | Health Check |
|---------|-----------|-----------|-------------|--------------|
| **gateway** | 8080 | — | API Gateway / Load Balancer | `GET /health` |
| **auth-service** | — | 50051 (host) | Authentication & JWT | TCP port 50052 |
| **user-service** | — | 50052 (host) | User profiles & addresses | TCP port 50053 |
| **catalog-service** | 8084 | 50053 (host) | Products, categories, brands | `GET /health` |
| **cart-service** | 8081 | 50054 (host) | Shopping cart management | `GET /health` |
| **order-service** | 8085 | 50055 (host) | Order lifecycle | `GET /health` |
| **payment-service** | 8082 | 50056 (host) | Payment processing (Stripe/YooMoney) | TCP port 50056 |
| **notification-service** | 8086 | 50057 (host) | Email, push, SMS notifications | TCP port 50057 |
| **search-service** | 8087 | 50058 (host) | Elasticsearch-based search | TCP port 50058 |
| **seller-service** | 8090 | 19090 (host) | Seller management | `GET /health` |
| **admin-service** | 8088 | — | Admin dashboard & management | `GET /health` |
| **bff-service** | 8089 | — | Backend-for-Frontend aggregation | `GET /health` |

### Infrastructure Services

| Service | Port | Description | Health Check |
|---------|------|-------------|--------------|
| **postgres** | 15432 | PostgreSQL 16 database | `pg_isready` |
| **redis** | 6379 | Redis 7 cache | `redis-cli ping` |
| **elasticsearch** | 9200 | Elasticsearch 8.12 | Cluster health endpoint |
| **kibana** | 5601 | Kibana dashboard | HTTP health check |
| **kafka** | 9092 | Kafka broker | `kafka-broker-api-versions` |
| **zookeeper** | 2181 | Zookeeper (Kafka) | `srvr` command |
| **mailhog** | 1025/8025 | Dev SMTP server | HTTP port check |
| **prometheus** | 9090 | Metrics collection | `/-/ready` |
| **grafana** | 3000 | Dashboards & alerting | `/api/health` |

---

## Infrastructure

### Databases

Each service owns its own PostgreSQL database:

| Database | Service | Purpose |
|----------|---------|---------|
| `auth_db` | auth-service | User credentials, sessions, JWT blacklists |
| `user_db` | user-service | User profiles, addresses, wishlists |
| `catalog_db` | catalog-service | Products, categories, brands, tags |
| `cart_db` | cart-service | Shopping cart items, saved items |
| `order_db` | order-service | Orders, order items, shipping |
| `payment_db` | payment-service | Payments, refunds, payment methods |
| `notification_db` | notification-service | Notification history, preferences |
| `search_db` | search-service | Search index metadata |
| `seller_db` | seller-service | Seller profiles, accounts, documents |
| `admin_db` | admin-service | Admin users, audit logs |

### Caching Strategy

| Service | Redis DB | TTL | Purpose |
|---------|----------|-----|---------|
| auth-service | 0 | 3600s | JWT blacklist, sessions |
| catalog-service | 1 | — | Product/category cache |
| cart-service | 3 | 86400s | Cart data, saved items |
| notification-service | 4 | 86400s | Notification queue |
| bff-service | 5 | 3600s | Aggregation cache |

### Kafka Topics

| Topic | Producer | Consumers | Description |
|-------|----------|-----------|-------------|
| `order.created` | order-service | notification-service | New order events |
| `order.status_changed` | order-service | notification-service | Order status updates |
| `payment.completed` | payment-service | notification-service | Successful payments |
| `payment.failed` | payment-service | notification-service | Failed payments |
| `marketplace-events` | — | — | General marketplace events |

---

## API Documentation

| Document | Path | Description |
|----------|------|-------------|
| API Index | [docs/index.md](docs/index.md) | Central navigation |
| Authentication | [docs/authentication.md](docs/authentication.md) | JWT, API keys, OAuth2 |
| Gateway | [docs/gateway.md](docs/gateway.md) | Routes, rate limiting, CORS |
| Services Overview | [docs/services.md](docs/services.md) | Service graph, dependencies |
| Development | [docs/development.md](docs/development.md) | Local setup guide |
| Deployment | [docs/deployment.md](docs/deployment.md) | Production deployment |
| Monitoring | [docs/monitoring.md](docs/monitoring.md) | Prometheus, Grafana, alerting |
| Auth Service API | [docs/api/auth-service.md](docs/api/auth-service.md) | gRPC + HTTP endpoints |
| Catalog Service API | [docs/api/catalog-service.md](docs/api/catalog-service.md) | HTTP + gRPC endpoints |
| Order Service API | [docs/api/order-service.md](docs/api/order-service.md) | gRPC + HTTP endpoints |
| Payment Service API | [docs/api/payment-service.md](docs/api/payment-service.md) | HTTP + gRPC endpoints |
| BFF Service API | [docs/api/bff-service.md](docs/api/bff-service.md) | HTTP aggregation endpoints |
| gRPC API Reference | [docs/grpc-api.md](docs/grpc-api.md) | All proto definitions |
| Kafka Events | [docs/kafka.md](docs/kafka.md) | Topics, schemas, patterns |

---

## Development Guide

### Local Setup

```bash
# 1. Clone and enter the project
cd migration_plan

# 2. Copy environment variables
cp .env.example .env

# 3. Start infrastructure
docker compose --profile dev up -d

# 4. Run migrations for a service
make migrate service=auth-service

# 5. Run tests for a service
make test service=auth-service
```

### Running Individual Services

```bash
# Run a specific service standalone
cd 01-auth-service
uvicorn src.main:app --host 0.0.0.0 --port 50052 --reload

# Run with Docker
docker compose --profile services up -d auth-service
```

### Code Style

- **Linting:** `make lint` or `make lint service=<name>`
- **Formatting:** Ruff (auto-applied)
- **Type Checking:** Mypy (per-service)
- **Imports:** Sorted by Ruff

### Debugging

```bash
# Open bash in a container
make bash service=gateway

# View live logs
make logs service=gateway

# Check service health
make health
```

### CI/CD

See [docs/deployment.md](docs/deployment.md) for CI/CD pipeline details.

---

## Deployment Guide

### Production Requirements

1. **TLS/SSL** — Enable for all external endpoints
2. **Secrets Management** — Use Vault, AWS Secrets Manager, or equivalent
3. **Database Backups** — Automated daily backups with 30-day retention
4. **Monitoring** — Prometheus + Grafana with alerting
5. **Log Aggregation** — Elasticsearch + Kibana or equivalent

See [docs/deployment.md](docs/deployment.md) for full details.

---

## Monitoring

### Stack

| Component | Port | URL (local) |
|-----------|------|-------------|
| Prometheus | 9090 | http://localhost:9090 |
| Grafana | 3000 | http://localhost:3000 (admin/admin) |
| Kibana | 5601 | http://localhost:5601 |

### Key Metrics

- **HTTP request rate & latency** (per service)
- **gRPC request rate & latency** (per service)
- **Database connection pool utilization**
- **Redis hit/miss ratio**
- **Kafka consumer lag**
- **Service health status**
- **Error rates** (4xx, 5xx)

See [docs/monitoring.md](docs/monitoring.md) for full monitoring guide.

---

## Troubleshooting

### Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Services fail to start | Infrastructure not ready | `docker compose --profile infra up -d` and wait |
| Port conflicts | Local PostgreSQL on 5432 | Infra uses 15432; adjust if needed |
| Kafka not connecting | Zookeeper not healthy | `docker compose --profile infra ps` |
| Auth fails | JWT_SECRET not set | Set `JWT_SECRET` in `.env` |
| Cart empty after refresh | Redis not connected | Verify `REDIS_HOST=redis` in `.env` |
| Search returns nothing | Elasticsearch not indexed | Run catalog reindex endpoint |

### Health Checks

```bash
make health
```

### Log Aggregation

All services output structured JSON logs. Forward to Elasticsearch for Kibana aggregation:

```bash
docker compose --profile monitoring up -d
# Access Kibana at http://localhost:5601
```

---

## Contributing

### Guidelines

1. **Branching:** Create feature branches from `main` (`feature/<name>`, `fix/<name>`)
2. **Commits:** Use [Conventional Commits](https://www.conventionalcommits.org/) format
   - `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `ci:`
3. **Code Style:** Follow Ruff linting rules; run `make lint` before PR
4. **Tests:** Write tests for new features; maintain ≥80% coverage
5. **Documentation:** Update relevant docs for API or behavior changes
6. **PR Reviews:** Require at least one approval; all checks must pass

### Checklist

- [ ] Code follows style guide (`make lint`)
- [ ] Tests pass (`make test`)
- [ ] Documentation updated
- [ ] No new dependencies without approval
- [ ] Environment variables documented in `.env.example`
- [ ] Migration files included (if schema changes)

---

## License

Internal project — all rights reserved.
