# АТОМАРНЫЙ ПЛАН МИГРАЦИИ HyperScale Marketplace: Go -> Python

## Как использовать этот план

Каждая задача — это атомарный шаг, который можно выполнить последовательно.
Задачи помечены номером `T-NNN`. Выполнять строго по порядку внутри каждой фазы.
Задачи в одной фазе, не имеющие зависимостей, можно выполнять параллельно.

---

## ⚠️ ОБНОВЛЕНИЕ: Проверка портов (исправлено)

### Конфликты обнаружены (проверка: 2026-08-01)

| Порт | Статус | Причина | Решение |
|---|---|---|---|
| **5432** | **ЗАНЯТ** | PostgreSQL уже запущен (PID 5936) — это оригинальный проект | Использовать порт **15432** для миграции |
| **7680** | **ЗАНЯТ** | svchost (PID 17668) — системный сервис | Убрать из плана, не использовать |

### Примечание по порту 8083
Порт 8083 на HOST занят System process (PID 4), но в оригинальном docker-compose search-service HTTP был на **8087:8083** (host:container), а не 8083. Порт 8087 свободен — оставляем как в оригинале.

### Изменённая карта портов (host:container)

| Порт (хост) | Порт (контейнер) | Сервис | Примечание |
|---|---|---|---|
| **15432** | 5432 | postgres | **ИЗМЕНЁН** с 5432 из-за конфликта |
| 6379 | 6379 | redis | OK |
| 9200 | 9200 | elasticsearch | OK |
| 5601 | 5601 | kibana | OK |
| 2181 | 2181 | zookeeper | OK |
| 9092 | 9092 | kafka | OK |
| 1025 | 1025 | mailhog | OK |
| 8025 | 8025 | mailhog | OK |
| 9090 | 9090 | prometheus | OK |
| 3000 | 3000 | grafana | OK |
| **8080** | **8080** | **gateway** | OK |
| **50051** | **50052** | **auth-service** | OK |
| **50052** | **50053** | **user-service** | OK |
| **50053** | **50051** | **catalog-service** | OK |
| **50054** | **50050** | **cart-service** | OK |
| **50055** | **50055** | **order-service** | OK |
| **50056** | **50056** | **payment-service** | OK |
| **50057** | **50057** | **notification-service** | OK |
| **50058** | **50058** | **search-service** | OK |
| **8081** | **8081** | **cart-service** | OK |
| **8082** | **8082** | **payment-service** | OK |
| **8087** | **8083** | **search-service** | OK (совпадает с оригиналом) |
| **8084** | **8080** | **catalog-service** | OK |
| **8085** | **8085** | **bff-service** | OK |
| **8086** | **8086** | **notification-service** | OK |
| **8088** | **8085** | **admin-service** | OK |
| **8089** | **8085** | **bff-service** | OK |
| **8090** | **8085** | **seller-service (HTTP)** | OK |
| **19090** | **9090** | **seller-service (gRPC)** | **ИЗМЕНЁН** (было 9090, конфликт с Prometheus) |

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 0: ПОДГОТОВКА ОКРУЖЕНИЯ
# ═══════════════════════════════════════════════════════════

## T-001: Проверка Docker
**Описание:** Убедиться что Docker и Docker Compose работают
**Действия:**
  1. Выполнить `docker --version`
  2. Выполнить `docker compose version`
  3. Выполнить `docker info` — проверить что daemon запущен
**Критерий готовности:** Docker daemon отвечает, версии > 24.0
**Зависимости:** нет

## T-002: Проверка Python
**Описание:** Убедиться что Python 3.12+ установлен
**Действия:**
  1. Выполнить `python --version`
  2. Если нет — установить Python 3.12+
  3. Проверить pip: `pip --version`
**Критерий готовности:** Python >= 3.12, pip работает
**Зависимости:** нет

## T-003: Создание структуры директорий
**Описание:** Создать полную структуру папок для миграции
**Действия:**
  1. Создать корень: `C:\Users\andre\Desktop\project\migration_plan\`
  2. Создать 12 директорий сервисов (01-12)
  3. В каждой директории сервиса создать поддиректории: src/, src/models/, src/services/, src/repositories/, src/grpc_server/, src/schemas/, src/utils/, tests/
  4. Создать proto/ с поддиректориями для каждого сервиса
  5. Создать 00-infrastructure/postgres/init-db/
  6. Создать 00-infrastructure/monitoring/prometheus/
  7. Создать 00-infrastructure/monitoring/grafana/dashboards/
**Критерий готовности:** Все директории созданы
**Зависимости:** нет

## T-004: Перенос gRPC proto-файлов
**Описание:** Скопировать все .proto файлы из оригинального проекта
**Исходные файлы:**
  - `C:\Users\andre\Desktop\basic_project\projects\auth-service\proto\auth\v1\auth.proto` -> `proto\auth\v1\auth.proto`
  - `C:\Users\andre\Desktop\basic_project\projects\user-service\proto\user\v1\user.proto` -> `proto\user\v1\user.proto`
  - `C:\Users\andre\Desktop\basic_project\projects\catalog-service\proto\catalog\v1\catalog.proto` -> `proto\catalog\v1\catalog.proto`
  - `C:\Users\andre\Desktop\basic_project\projects\cart-service\proto\cart\v1\cart.proto` -> `proto\cart\v1\cart.proto`
  - `C:\Users\andre\Desktop\basic_project\projects\order-service\proto\order\v1\order.proto` -> `proto\order\v1\order.proto`
  - `C:\Users\andre\Desktop\basic_project\projects\payment-service\proto\payment\v1\payment.proto` -> `proto\payment\v1\payment.proto`
  - `C:\Users\andre\Desktop\basic_project\projects\notification-service\proto\notification\v1\notification.proto` -> `proto\notification\v1\notification.proto`
  - `C:\Users\andre\Desktop\basic_project\projects\search-service\proto\search\v1\search.proto` -> `proto\search\v1\search.proto`
  - `C:\Users\andre\Desktop\basic_project\projects\seller-service\proto\seller\v1\seller.proto` -> `proto\seller\v1\seller.proto`
  - `C:\Users\andre\Desktop\basic_project\projects\bff-service\proto\bff\v1\bff.proto` -> `proto\bff\v1\bff.proto`
**Критерий готовности:** 10 proto-файлов в директории proto/
**Зависимости:** T-003

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 1: ИНФРАСТРУКТУРА
# ═══════════════════════════════════════════════════════════

## T-101: Init-скрипт PostgreSQL
**Описание:** Создать SQL-скрипт инициализации баз данных
**Файл:** `00-infrastructure/postgres/init-db/01-init-databases.sql`
**Содержимое:**
  - CREATE DATABASE для каждой из 10 БД: auth_db, user_db, catalog_db, cart_db, order_db, payment_db, notification_db, search_db, seller_db, admin_db
  - GRANT ALL PRIVILEGES для postgres
**Важно:** PostgreSQL будет запущен на порту **15432** (не 5432) из-за конфликта с локальным PostgreSQL
**Критерий готовности:** SQL-файл создан
**Зависимости:** T-003

## T-102: Конфиг Prometheus
**Описание:** Создать prometheus.yml с job'ами для всех сервисов
**Файл:** `00-infrastructure/monitoring/prometheus/prometheus.yml`
**Содержимое:**
  - global scrape_interval: 15s
  - 12 scrape_configs: для каждого сервиса (auth, user, catalog, cart, order, payment, notification, search, seller, admin, bff, gateway)
**Критерий готовности:** YAML-файл валиден
**Зависимости:** T-003

## T-103: unified-docker-compose.yml (инфраструктура)
**Описание:** Создать docker-compose с сервисами инфраструктуры
**Файл:** `unified-docker-compose.yml`
**Сервисы инфраструктуры:**
  1. postgres (port 5432, image postgres:16-alpine, 1G memory)
  2. redis (port 6379, image redis:7-alpine, 512M memory)
  3. elasticsearch (port 9200, image elasticsearch:8.12.0, 2G memory)
  4. kibana (port 5601, image kibana:8.12.0, depends_on elasticsearch)
  5. zookeeper (port 2181, image confluentinc/cp-zookeeper:7.5.0)
  6. kafka (port 9092, image confluentinc/cp-kafka:7.5.0, depends_on zookeeper)
  7. mailhog (ports 1025,8025, image mailhog/mailhog:v1.0.1)
  8. prometheus (port 9090, image prom/prometheus:v2.48.0)
  9. grafana (port 3000, image grafana/grafana:10.1.0, depends_on prometheus)
**Сеть:** marketplace (bridge)
**Volumes:** postgres-data, redis-data, elasticsearch-data, prometheus-data, grafana-data
**Критерий готовности:** docker compose config валиден
**Зависимости:** T-101, T-102

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 2: AUTH SERVICE (Фаза 1 — нет внешних зависимостей)
# ═══════════════════════════════════════════════════════════

## T-201: Auth — pyproject.toml
**Описание:** Создать файл зависимостей для auth-service
**Файл:** `01-auth-service/pyproject.toml`
**Ключевые зависимости:**
  - python ^3.12
  - fastapi ^0.109.0, uvicorn ^0.27.0
  - grpcio ^1.62.0, grpcio-tools ^1.62.0, protobuf ^5.25.0
  - sqlalchemy ^2.0.25, asyncpg ^0.29.0
  - redis ^5.0.1
  - pydantic ^2.5.0, pydantic-settings ^2.1.0
  - python-jose ^3.3.0, passlib[bcrypt] ^1.7.4
  - httpx ^0.26.0
  - pytest ^8.0.0, pytest-asyncio ^0.23.0
**Критерий готовности:** Файл создан
**Зависимости:** T-003

## T-201.1: Auth — DB_PORT исправление
**Описание:** Убедиться что DB_PORT=5432 (внутри Docker-сети, не хоста)
**Важно:** Внутри docker-compose сеть `marketplace`, все сервисы общаются по внутреннему порту 5432.
Конфликт только на уровне хоста (15432:5432). Внутри сети — 5432.
**Зависимости:** T-201

## T-202: Auth — Dockerfile
**Описание:** Создать Dockerfile для auth-service
**Файл:** `01-auth-service/Dockerfile`
**Содержимое:**
  - FROM python:3.12-slim
  - WORKDIR /app
  - COPY pyproject.toml ./
  - pip install .
  - COPY src/ ./src/
  - CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "50052"]
**Критерий готовности:** Dockerfile валиден
**Зависимости:** T-201

## T-203: Auth — .env.example
**Описание:** Создать шаблон переменных окружения
**Файл:** `01-auth-service/.env.example`
**Переменные:**
  - GRPC_PORT=50052
  - DB_HOST=postgres, DB_PORT=5432, DB_USER=postgres, DB_PASSWORD=postgres, DB_NAME=auth_db, DB_SSL_MODE=disable
  - REDIS_HOST=redis, REDIS_PORT=6379, REDIS_DB=0
  - JWT_SECRET=change-me-in-production, JWT_EXPIRY=3600
  - LOG_LEVEL=info
**Критерий готовности:** Файл создан
**Зависимости:** T-003

## T-204: Auth — config.py
**Описание:** Создать модуль конфигурации через pydantic-settings
**Файл:** `01-auth-service/src/config.py`
**Класс Settings:**
  - grpc_port: int = 50052
  - db_host, db_port, db_user, db_password, db_name, db_ssl_mode
  - redis_host, redis_port, redis_db
  - jwt_secret: str, jwt_expiry: int = 3600
  - log_level: str = "info"
  - Метод: get_db_url() -> str (возвращает postgresql+asyncpg://...)
  - Метод: get_redis_url() -> str
**Критерий готовности:** Settings загружается из environ
**Зависимости:** T-201

## T-205: Auth — SQLAlchemy модели
**Описание:** Создать модели БД для auth
**Файл:** `01-auth-service/src/models/user.py`
**Модели:**
  - class User(Base): id (UUID), email, hashed_password, first_name, last_name, role, created_at, updated_at
  - class RefreshToken(Base): id, user_id, token, expires_at, created_at
**Критерий готовности:** Модели определены, Base для импорта
**Зависимости:** T-204

## T-206: Auth — Database engine
**Описание:** Создать модуль подключения к БД
**Файл:** `01-auth-service/src/database.py`
**Содержимое:**
  - async_engine = create_async_engine()
  - async_session = sessionmaker()
  - get_db(): асинхронный генератор сессий
  - init_db(): create_all() для тестов
**Критерий готовности:** Функции возвращают engine/session
**Зависимости:** T-204, T-205

## T-207: Auth — Password service
**Описание:** Создать сервис хеширования паролей
**Файл:** `01-auth-service/src/services/password_service.py`
**Функции:**
  - hash_password(plain: str) -> str (bcrypt)
  - verify_password(plain: str, hashed: str) -> bool
  - generate_token() -> str (secrets.token_urlsafe)
**Критерий готовности:** Функции работают с bcrypt
**Зависимации:** T-201

## T-208: Auth — JWT service
**Описание:** Создать сервис работы с JWT
**Файл:** `01-auth-service/src/services/jwt_service.py`
**Функции:**
  - create_access_token(user_id, email, secret, expiry) -> str (python-jose)
  - create_refresh_token(user_id, secret, expiry) -> str
  - decode_token(token, secret) -> dict
  - verify_token(token, secret) -> dict
**Критерий готовности:** Токены создаются и валидируются
**Зависимости:** T-201

## T-209: Auth — Auth repository
**Описание:** Создать репозиторий для auth
**Файл:** `01-auth-service/src/repositories/auth_repository.py`
**Методы:**
  - async def get_user_by_email(db, email) -> User | None
  - async def create_user(db, email, hashed_password, first_name, last_name) -> User
  - async def create_refresh_token(db, user_id, token, expires_at) -> RefreshToken
  - async def get_refresh_token(db, token) -> RefreshToken | None
  - async def revoke_refresh_token(db, token) -> bool
  - async def revoke_user_tokens(db, user_id) -> int
**Критерий готовности:** Все методы асинхронные, с asyncpg
**Зависимости:** T-205, T-206

## T-210: Auth — Auth service (бизнес-логика)
**Описание:** Создать сервис бизнес-логики auth
**Файл:** `01-auth-service/src/services/auth_service.py`
**Методы:**
  - async def register(email, password, first_name, last_name) -> dict (создаёт пользователя, хеширует пароль, возвращает user)
  - async def login(email, password) -> dict (находит пользователя, проверяет пароль, создаёт refresh token, возвращает tokens + user)
  - async def refresh(refresh_token) -> dict (валидирует refresh, создаёт новый access + refresh, инвалидирует старый)
  - async def logout(refresh_token) -> dict (инвалидирует refresh)
  - async def forgot_password(email) -> dict (генерирует reset token, отправляет email)
**Критерий готовности:** Все методы проходят unit-тесты
**Зависимости:** T-207, T-208, T-209

## T-211: Auth — gRPC server
**Описание:** Создать gRPC сервер для auth-service
**Файл:** `01-auth-service/src/grpc_server/server.py`
**Содержимое:**
  - Сервис: AuthServicer(grpc.ServiceMethod)
  - Реализация всех RPC: Register, Login, Refresh, Logout, ForgotPassword
  - server = grpc.server(futures.ThreadPoolExecutor)
  - auth_pb2.add_AuthServiceServicer_to_server(servicer, server)
  - server.add_insecure_port(f'0.0.0.0:{port}')
  - server.start() / server.wait_for_termination()
**Критерий готовности:** gRPC сервер запускается и слушает порт
**Зависимости:** T-204

## T-212: Auth — gRPC proto bindings
**Описание:** Сгенерировать Python-код из auth.proto
**Команда:**
  ```
  python -m grpc_tools.protoc -I ../proto --python_out=. --grpc_python_out=. --pyi_out=. ../proto/auth/v1/auth.proto
  ```
**Файлы:**
  - `01-auth-service/src/grpc_server/auth_pb2.py`
  - `01-auth-service/src/grpc_server/auth_pb2_grpc.py`
**Критерий готовности:** Файлы сгенерированы, импортируются
**Зависимости:** T-211

## T-213: Auth — main.py
**Описание:** Точка входа для auth-service
**Файл:** `01-auth-service/src/main.py`
**Содержимое:**
  - from fastapi import FastAPI
  - app = FastAPI(title="Auth Service")
  - @app.get("/health") -> {"status": "ok"}
  - @app.on_event("startup"): start_grpc_server()
  - @app.on_event("shutdown"): stop_grpc_server()
  - uvicorn.run(app, host="0.0.0.0", port=50052)
**Критерий готовности:** Сервер запускается, health-check отвечает
**Зависимости:** T-204, T-211

## T-214: Auth — Тесты
**Описание:** Написать unit-тесты для auth
**Файлы:**
  - `01-auth-service/tests/conftest.py` — fixtures для async_engine, db session
  - `01-auth-service/tests/test_auth_service.py` — тесты register, login, refresh, logout
  - `01-auth-service/tests/test_jwt.py` — тесты create/verify token
**Критерий готовности:** pytest запускается, все тесты проходят
**Зависимости:** T-210, T-213

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 3: CATALOG SERVICE (Фаза 1 — нет внешних зависимостей, параллельно с Фазой 2)
# ═══════════════════════════════════════════════════════════

## T-301: Catalog — pyproject.toml
**Описание:** Создать файл зависимостей
**Файл:** `03-catalog-service/pyproject.toml`
**Ключевые зависимости:** fastapi, uvicorn, grpcio, sqlalchemy, asyncpg, redis, pydantic, httpx, alembic
**Критерий готовности:** Файл создан
**Зависимости:** T-003

## T-302: Catalog — Dockerfile
**Описание:** Создать Dockerfile
**Файл:** `03-catalog-service/Dockerfile`
**Порты:** HTTP 8080, gRPC 50051
**Критерий готовности:** Dockerfile валиден
**Зависимости:** T-301

## T-303: Catalog — .env.example
**Описание:** Шаблон переменных
**Файл:** `03-catalog-service/.env.example`
**Переменные:** SERVER_PORT=8080, GRPC_PORT=50051, DB_*, REDIS_*, LOG_LEVEL
**Критерий готовности:** Файл создан
**Зависимости:** T-003

## T-304: Catalog — config.py
**Описание:** Модуль конфигурации
**Файл:** `03-catalog-service/src/config.py`
**Класс Settings:** server_port, grpc_port, db_*, redis_*, log_level
**Критерий готовности:** Settings загружается
**Зависимости:** T-301

## T-305: Catalog — SQLAlchemy модели
**Описание:** Создать модели БД
**Файл:** `03-catalog-service/src/models/`
**Модели:**
  - Category: id, name, slug, description, parent_id, level, path, is_active, created_at, updated_at
  - Brand: id, name, slug, description, logo_url, is_active, created_at, updated_at
  - Tag: id, name, slug, description, is_active, created_at, updated_at
  - Product: id, name, slug, description, sku, barcode, category_id, brand_id, seller_id, status, price, compare_at_price, cost_price, quantity, is_active, is_featured, image_urls (JSONB), tag_ids (JSONB), metadata (JSONB), created_at, updated_at, deleted_at
  - ProductTag: product_id, tag_id
**Критерий готовности:** Все модели определены
**Зависимости:** T-304

## T-306: Catalog — Database engine
**Описание:** Подключение к БД
**Файл:** `03-catalog-service/src/database.py`
**Содержимое:** async_engine, async_session, get_db
**Критерий готовности:** Функции работают
**Зависимости:** T-304

## T-307: Catalog — Alembic migration files
**Описание:** SQL-миграции
**Файлы:**
  - `03-catalog-service/migrations/001_create_categories.up.sql`
  - `03-catalog-service/migrations/001_create_categories.down.sql`
  - `03-catalog-service/migrations/002_create_tags.up.sql`
  - `03-catalog-service/migrations/002_create_tags.down.sql`
  - `03-catalog-service/migrations/003_create_products.up.sql`
  - `03-catalog-service/migrations/003_create_products.down.sql`
**Критерий готовности:** SQL-файлы создают/удаляют таблицы
**Зависимости:** T-305

## T-308: Catalog — Repositories
**Описание:** Репозитории для CRUD
**Файлы:**
  - `src/repositories/category_repository.py`: create, get_by_id, get_by_slug, get_tree, get_children, list, update, delete
  - `src/repositories/brand_repository.py`: create, get_by_id, get_by_slug, list, search, update, delete
  - `src/repositories/tag_repository.py`: create, get_by_id, get_by_slug, list, update, delete
  - `src/repositories/product_repository.py`: create, get_by_id, get_by_slug, list (с фильтрами), search, update, delete, get_by_category, get_by_tag
**Критерий готовности:** Все CRUD-методы асинхронные
**Зависимости:** T-305, T-306

## T-309: Catalog — Services (бизнес-логика)
**Описание:** Сервисы
**Файлы:**
  - `src/services/category_service.py`: create_category, get_category, get_category_tree, get_category_children, list_categories, update_category, delete_category
  - `src/services/brand_service.py`: create_brand, get_brand, list_brands, search_brands, update_brand, delete_brand
  - `src/services/tag_service.py`: create_tag, get_tag, list_tags, update_tag, delete_tag
  - `src/services/product_service.py`: create_product, get_product, list_products, search_products, update_product, delete_product, get_by_category, get_by_tag
**Критерий готовности:** Бизнес-логика реализована
**Зависимости:** T-308

## T-310: Catalog — gRPC server
**Описание:** Реализация gRPC service
**Файл:** `03-catalog-service/src/grpc_server/catalog_pb2_service.py`
**RPC:** CreateCategory, GetCategory, UpdateCategory, DeleteCategory, ListCategories, GetCategoryTree, GetCategoryChildren, CreateBrand, GetBrand, UpdateBrand, DeleteBrand, ListBrands, SearchBrands, CreateTag, GetTag, UpdateTag, DeleteTag, ListTags, CreateProduct, GetProduct, UpdateProduct, DeleteProduct, ListProducts, SearchProducts, GetProductsByCategory, GetProductsByTag
**Критерий готовности:** Все RPC вызывают сервисы
**Зависимости:** T-309

## T-311: Catalog — gRPC proto bindings
**Описание:** Генерация из catalog.proto
**Команда:** `python -m grpc_tools.protoc -I ../proto --python_out=. --grpc_python_out=. --pyi_out=. ../proto/catalog/v1/catalog.proto`
**Критерий готовности:** Файлы сгенерированы
**Зависимости:** T-310

## T-312: Catalog — HTTP API endpoints
**Описание:** REST-эндпоинты через FastAPI
**Файлы:**
  - `src/api/categories.py`: GET /categories, GET /categories/{id}, POST /categories, PUT /categories/{id}, DELETE /categories/{id}, GET /categories/tree, GET /categories/{id}/children
  - `src/api/brands.py`: GET /brands, GET /brands/{id}, POST /brands, PUT /brands/{id}, DELETE /brands/{id}, GET /brands/search
  - `src/api/tags.py`: GET /tags, GET /tags/{id}, POST /tags, PUT /tags/{id}, DELETE /tags/{id}
  - `src/api/products.py`: GET /products, GET /products/{id}, POST /products, PUT /products/{id}, DELETE /products/{id}, GET /products/search, GET /products/category/{id}, GET /products/tag/{id}
**Критерий готовности:** Все эндпоинты возвращают данные
**Зависимости:** T-309

## T-313: Catalog — Schemas (Pydantic)
**Описание:** Pydantic-схемы для валидации
**Файлы:**
  - `src/schemas/category.py`: CategoryCreate, CategoryUpdate, CategoryResponse
  - `src/schemas/brand.py`: BrandCreate, BrandUpdate, BrandResponse
  - `src/schemas/tag.py`: TagCreate, TagUpdate, TagResponse
  - `src/schemas/product.py`: ProductCreate, ProductUpdate, ProductResponse
**Критерий готовности:** Схемы валидируют вход/выход
**Зависимости:** T-305

## T-314: Catalog — main.py
**Описание:** Точка входа
**Файл:** `03-catalog-service/src/main.py`
**Содержимое:** FastAPI app, health-check, gRPC server, routers
**Критерий готовности:** Сервер запускается, /health отвечает
**Зависимости:** T-310, T-312

## T-315: Catalog — Тесты
**Описание:** Unit-тесты
**Файлы:**
  - `tests/conftest.py`
  - `tests/test_category_service.py`
  - `tests/test_product_service.py`
**Критерий готовности:** pytest проходит
**Зависимости:** T-309, T-314

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 4: USER SERVICE (зависит от Auth)
# ═══════════════════════════════════════════════════════════

## T-401: User — pyproject.toml + Dockerfile + .env.example
**Описание:** Базовые файлы сервиса
**Файлы:** `02-user-service/pyproject.toml`, `02-user-service/Dockerfile`, `02-user-service/.env.example`
**Переменные:** GRPC_PORT=50053, DB_*, REDIS_DB=2, AUTH_SERVICE_HOST=auth-service, AUTH_SERVICE_PORT=50052
**Критерий готовности:** Файлы созданы
**Зависимости:** T-003

## T-402: User — config.py
**Описание:** Конфигурация
**Файл:** `02-user-service/src/config.py`
**Критерий готовности:** Settings загружается
**Зависимости:** T-401

## T-403: User — SQLAlchemy модели
**Описание:** Модели БД
**Модели:**
  - User: id, email, phone, first_name, last_name, avatar_url, role, created_at, updated_at
  - Address: id, user_id, type, full_name, line1, line2, city, postal_code, country, is_default, created_at, updated_at
  - WishlistItem: id, user_id, product_id, added_at
**Критерий готовности:** Модели определены
**Зависимости:** T-402

## T-404: User — Database engine
**Описание:** Подключение к БД
**Файл:** `02-user-service/src/database.py`
**Критерий готовности:** async_engine, get_db работают
**Зависимости:** T-402

## T-405: User — gRPC client для Auth
**Описание:** Клиент для вызова Auth Service
**Файл:** `02-user-service/src/grpc_client/auth_client.py`
**Методы:**
  - async def verify_token(token) -> dict
  - async def get_user_from_token(token) -> dict
**Критерий готовности:** Клиент соединяется с auth-service:50052
**Зависимости:** T-402

## T-406: User — Repositories
**Описание:** Репозитории
**Файлы:**
  - `src/repositories/user_repository.py`: create, get_by_id, get_by_email, update
  - `src/repositories/address_repository.py`: create, get_by_id, get_by_user, update, delete, list, set_default
  - `src/repositories/wishlist_repository.py`: add, get_by_user, remove, list
**Критерий готовности:** CRUD-методы работают
**Зависимости:** T-403, T-404

## T-407: User — Services (бизнес-логика)
**Описание:** Сервисы
**Файлы:**
  - `src/services/user_service.py`: get_user, update_user
  - `src/services/address_service.py`: add_address, update_address, delete_address, get_user_addresses
  - `src/services/wishlist_service.py`: add_to_wishlist, get_user_wishlist, remove_from_wishlist
**Критерий готовности:** Бизнес-логика реализована
**Зависимости:** T-405, T-406

## T-408: User — gRPC server
**Описание:** Реализация gRPC service
**Файл:** `02-user-service/src/grpc_server/user_pb2_service.py`
**RPC:** GetUser, UpdateUser, AddAddress, UpdateAddress, DeleteAddress, GetUserAddresses, AddToWishlist, GetUserWishlist, RemoveFromWishlist
**Критерий готовности:** Все RPC вызывают сервисы
**Зависимости:** T-407

## T-409: User — gRPC proto bindings
**Описание:** Генерация из user.proto
**Команда:** `python -m grpc_tools.protoc -I ../proto --python_out=. --grpc_python_out=. --pyi_out=. ../proto/user/v1/user.proto`
**Критерий готовности:** Файлы сгенерированы
**Зависимости:** T-408

## T-410: User — main.py
**Описание:** Точка входа
**Файл:** `02-user-service/src/main.py`
**Критерий готовности:** Сервер запускается
**Зависимости:** T-408, T-409

## T-411: User — Тесты
**Описание:** Unit-тесты
**Файлы:** `02-user-service/tests/test_user_service.py`, `tests/test_address_service.py`, `tests/test_wishlist_service.py`
**Критерий готовности:** pytest проходит
**Зависимости:** T-407, T-410

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 5: CART SERVICE (зависит от Auth + Catalog)
# ═══════════════════════════════════════════════════════════

## T-501: Cart — pyproject.toml + Dockerfile + .env.example
**Описание:** Базовые файлы
**Файлы:** `04-cart-service/pyproject.toml`, `04-cart-service/Dockerfile`, `04-cart-service/.env.example`
**Переменные:** GRPC_PORT=50050, SERVER_PORT=8081, DB_*, REDIS_DB=3, REDIS_CART_TTL=86400, REDIS_SAVED_TTL=2592000, CATALOG_SERVICE_HOST=catalog-service, CATALOG_SERVICE_PORT=50051
**Критерий готовности:** Файлы созданы
**Зависимости:** T-003

## T-502: Cart — config.py
**Описание:** Конфигурация
**Файл:** `04-cart-service/src/config.py`
**Критерий готовности:** Settings загружается
**Зависимости:** T-501

## T-503: Cart — gRPC клиенты
**Описание:** Клиенты для внешних сервисов
**Файлы:**
  - `src/grpc_client/auth_client.py`: verify_token
  - `src/grpc_client/catalog_client.py`: get_product(product_id) -> Product
**Критерий готовности:** Клиенты соединяются с auth и catalog
**Зависимости:** T-502

## T-504: Cart — Redis client
**Описание:** Работа с Redis для корзины
**Файл:** `04-cart-service/src/redis_client.py`
**Методы:**
  - get_cart(user_id) -> dict
  - set_cart(user_id, cart_data, ttl) -> None
  - add_item(user_id, item) -> None
  - update_item(user_id, product_id, quantity) -> None
  - remove_item(user_id, product_id) -> None
  - clear_cart(user_id) -> None
  - save_for_later(user_id, product_id, item_data) -> None
  - move_to_cart(user_id, product_id) -> None
**Критерий готовности:** Redis-операции работают
**Зависимости:** T-502

## T-505: Cart — Services (бизнес-логика)
**Описание:** Сервисы корзины
**Файл:** `04-cart-service/src/services/cart_service.py`
**Методы:**
  - get_cart(user_id): получает данные из Redis, дополняет ценами из Catalog
  - add_item(user_id, product_id, quantity): добавляет товар, запрашивает цену у Catalog
  - update_item(user_id, product_id, quantity): обновляет количество
  - remove_item(user_id, product_id): удаляет товар
  - clear_cart(user_id): очищает корзину
  - save_for_later(user_id, product_id): переносит в saved
  - move_to_cart(user_id, product_id): возвращает из saved
**Критерий готовности:** Все методы работают
**Зависимости:** T-503, T-504

## T-506: Cart — gRPC server
**Описание:** Реализация gRPC service
**Файл:** `04-cart-service/src/grpc_server/cart_pb2_service.py`
**RPC:** GetCart, AddItem, UpdateItem, RemoveItem, ClearCart, SaveForLater, MoveToCart
**Критерий готовности:** Все RPC работают
**Зависимости:** T-505

## T-507: Cart — gRPC proto bindings
**Описание:** Генерация из cart.proto
**Команда:** `python -m grpc_tools.protoc -I ../proto --python_out=. --grpc_python_out=. --pyi_out=. ../proto/cart/v1/cart.proto`
**Критерий готовности:** Файлы сгенерированы
**Зависимости:** T-506

## T-508: Cart — HTTP API
**Описание:** REST-эндпоинты
**Файлы:** `04-cart-service/src/api/cart.py`
**Эндпоинты:** GET /cart, POST /cart/items, PUT /cart/items/{product_id}, DELETE /cart/items/{product_id}, POST /cart/clear, POST /cart/save-for-later, POST /cart/move-to-cart
**Критерий готовности:** Эндпоинты возвращают данные
**Зависимости:** T-505

## T-509: Cart — main.py
**Описание:** Точка входа
**Файл:** `04-cart-service/src/main.py`
**Критерий готовности:** Сервер запускается
**Зависимости:** T-506, T-507, T-508

## T-510: Cart — Тесты
**Описание:** Unit-тесты
**Файлы:** `04-cart-service/tests/test_cart_service.py`
**Критерий готовности:** pytest проходит
**Зависимости:** T-505, T-509

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 6: ORDER SERVICE (зависит от Auth + Cart + Catalog)
# ═══════════════════════════════════════════════════════════

## T-601: Order — pyproject.toml + Dockerfile + .env.example
**Описание:** Базовые файлы
**Файлы:** `05-order-service/pyproject.toml`, `05-order-service/Dockerfile`, `05-order-service/.env.example`
**Переменные:** GRPC_PORT=50055, DB_*, KAFKA_BROKERS=kafka:9092, KAFKA_ORDER_CREATED_TOPIC=order.created, KAFKA_ORDER_STATUS_CHANGED_TOPIC=order.status_changed, CART_SERVICE_HOST=cart-service, CART_SERVICE_PORT=50050, CATALOG_SERVICE_HOST=catalog-service, CATALOG_SERVICE_PORT=50051
**Критерий готовности:** Файлы созданы
**Зависимости:** T-003

## T-602: Order — config.py
**Описание:** Конфигурация
**Файл:** `05-order-service/src/config.py`
**Критерий готовности:** Settings загружается
**Зависимости:** T-601

## T-603: Order — SQLAlchemy модели
**Описание:** Модели БД
**Модели:**
  - Order: id, user_id, cart_id, status, total_amount, currency, shipping_address (JSONB), payment_method, tracking_number, cancelled_by, cancellation_reason, created_at, updated_at, completed_at, cancelled_at
  - OrderItem: id, order_id, product_id, product_name, sku, quantity, unit_price, total_price, image_url
**Критерий готовности:** Модели определены
**Зависимости:** T-602

## T-604: Order — Database engine
**Описание:** Подключение к БД
**Файл:** `05-order-service/src/database.py`
**Критерий готовности:** async_engine, get_db работают
**Зависимости:** T-602

## T-605: Order — gRPC клиенты
**Описание:** Клиенты для внешних сервисов
**Файлы:**
  - `src/grpc_client/auth_client.py`: verify_token
  - `src/grpc_client/cart_client.py`: get_cart(user_id) -> Cart
  - `src/grpc_client/catalog_client.py`: get_product(product_id) -> Product
**Критерий готовности:** Клиенты работают
**Зависимости:** T-602

## T-606: Order — Kafka producer
**Описание:** Отправка событий в Kafka
**Файл:** `05-order-service/src/kafka/publisher.py`
**Методы:**
  - async def publish_order_created(order_id, user_id, total_amount)
  - async def publish_order_status_changed(order_id, old_status, new_status)
**Критерий готовности:** Сообщения отправляются в Kafka
**Зависимости:** T-602

## T-607: Order — Repositories
**Описание:** Репозитории
**Файлы:**
  - `src/repositories/order_repository.py`: create, get_by_id, get_by_user, update_status, list
  - `src/repositories/order_item_repository.py`: create_batch, get_by_order
**Критерий готовности:** CRUD-методы работают
**Зависимости:** T-603, T-604

## T-608: Order — Services (бизнес-логика)
**Описание:** Сервисы
**Файл:** `05-order-service/src/services/order_service.py`
**Методы:**
  - async def create_order(user_id, cart_id, shipping_address, payment_method): валидирует корзину через Cart Service, создаёт заказ, отправляет event в Kafka
  - async def get_order(order_id)
  - async def get_user_orders(user_id, page, page_size, status)
  - async def cancel_order(order_id, user_id, reason)
  - async def update_order_status(order_id, status)
**Критерий готовности:** Бизнес-логика реализована
**Зависимости:** T-605, T-606, T-607

## T-609: Order — gRPC server
**Описание:** Реализация gRPC service
**Файл:** `05-order-service/src/grpc_server/order_pb2_service.py`
**RPC:** CreateOrder, GetOrder, GetUserOrders, CancelOrder, UpdateOrderStatus
**Критерий готовности:** Все RPC работают
**Зависимости:** T-608

## T-610: Order — gRPC proto bindings
**Описание:** Генерация из order.proto
**Команда:** `python -m grpc_tools.protoc -I ../proto --python_out=. --grpc_python_out=. --pyi_out=. ../proto/order/v1/order.proto`
**Критерий готовности:** Файлы сгенерированы
**Зависимости:** T-609

## T-611: Order — main.py
**Описание:** Точка входа
**Файл:** `05-order-service/src/main.py`
**Критерий готовности:** Сервер запускается
**Зависимости:** T-609, T-610

## T-612: Order — Тесты
**Описание:** Unit-тесты
**Файлы:** `05-order-service/tests/test_order_service.py`
**Критерий готовности:** pytest проходит
**Зависимости:** T-608, T-611

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 7: PAYMENT SERVICE (зависит от Order)
# ═══════════════════════════════════════════════════════════

## T-701: Payment — pyproject.toml + Dockerfile + .env.example
**Описание:** Базовые файлы
**Файлы:** `06-payment-service/pyproject.toml`, `06-payment-service/Dockerfile`, `06-payment-service/.env.example`
**Переменные:** DB_*, STRIPE_SECRET_KEY=sk_test_placeholder, STRIPE_WEBHOOK_SECRET=whsec_placeholder, YOOMONEY_SHOP_ID=, YOOMONEY_TOKEN=, KAFKA_BROKERS=kafka:9092, KAFKA_TOPIC=marketplace-events
**Критерий готовности:** Файлы созданы
**Зависимости:** T-003

## T-702: Payment — config.py
**Описание:** Конфигурация
**Файл:** `06-payment-service/src/config.py`
**Критерий готовности:** Settings загружается
**Зависимости:** T-701

## T-703: Payment — SQLAlchemy модели
**Описание:** Модели БД
**Модели:**
  - Payment: id, order_id, user_id, amount, currency, status (enum), provider (enum), provider_payment_id, provider_error, payment_method_id, created_at, updated_at, paid_at
  - PaymentMethod: id, user_id, type, last_four, expiry, is_default, created_at
  - Refund: id, payment_id, user_id, amount, currency, status, provider_refund_id, reason, created_at, refunded_at
**Критерий готовности:** Модели определены
**Зависимости:** T-702

## T-704: Payment — Database engine
**Описание:** Подключение к БД
**Файл:** `06-payment-service/src/database.py`
**Критерий готовности:** async_engine, get_db работают
**Зависимости:** T-702

## T-705: Payment — Stripe/YooMoney client
**Описание:** Клиент платёжных провайдеров
**Файлы:**
  - `src/stripe_client/stripe_client.py`: create_payment_intent, confirm_payment, refund_payment
  - `src/stripe_client/yoomoney_client.py`: create_payment, confirm_payment, refund_payment
**Критерий готовности:** Клиенты вызывают API провайдеров
**Зависимости:** T-702

## T-706: Payment — Kafka producer
**Описание:** Отправка событий
**Файл:** `06-payment-service/src/kafka/producer.py`
**Методы:**
  - async def publish_payment_completed(payment_id, order_id, amount)
  - async def publish_payment_failed(payment_id, order_id, error)
**Критерий готовности:** Сообщения отправляются
**Зависимости:** T-702

## T-707: Payment — Repositories
**Описание:** Репозитории
**Файлы:**
  - `src/repositories/payment_repository.py`: create, get_by_id, get_by_order, update_status, list
  - `src/repositories/payment_method_repository.py`: create, get_by_user, get_default, list
  - `src/repositories/refund_repository.py`: create, get_by_payment, list
**Критерий готовности:** CRUD-методы работают
**Зависимости:** T-703, T-704

## T-708: Payment — Services (бизнес-логика)
**Описание:** Сервисы
**Файл:** `06-payment-service/src/services/payment_service.py`
**Методы:**
  - async def create_payment(order_id, user_id, payment_method_id, currency, amount, provider)
  - async def confirm_payment(payment_id, provider_data)
  - async def get_payment(payment_id)
  - async def refund_payment(payment_id, amount, reason)
  - async def get_user_payments(user_id, page, page_size, status_filter)
  - async def webhook(event_type, payload)
**Критерий готовности:** Бизнес-логика реализована
**Зависимости:** T-705, T-706, T-707

## T-709: Payment — gRPC server
**Описание:** Реализация gRPC service
**Файл:** `06-payment-service/src/grpc_server/payment_pb2_service.py`
**RPC:** CreatePayment, ConfirmPayment, GetPayment, RefundPayment, GetUserPayments, Webhook
**Критерий готовности:** Все RPC работают
**Зависимости:** T-708

## T-710: Payment — gRPC proto bindings
**Описание:** Генерация из payment.proto
**Команда:** `python -m grpc_tools.protoc -I ../proto --python_out=. --grpc_python_out=. --pyi_out=. ../proto/payment/v1/payment.proto`
**Критерий готовности:** Файлы сгенерированы
**Зависимости:** T-709

## T-711: Payment — HTTP API (webhook endpoint)
**Описание:** REST-эндпоинт для webhook
**Файл:** `06-payment-service/src/api/webhook.py`
**Эндпоинт:** POST /webhook/stripe
**Критерий готовности:** Webhook обрабатывается
**Зависимости:** T-708

## T-712: Payment — main.py
**Описание:** Точка входа
**Файл:** `06-payment-service/src/main.py`
**Критерий готовности:** Сервер запускается
**Зависимости:** T-709, T-710, T-711

## T-713: Payment — Тесты
**Описание:** Unit-тесты
**Файлы:** `06-payment-service/tests/test_payment_service.py`
**Критерий готовности:** pytest проходит
**Зависимости:** T-708, T-712

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 8: SEARCH SERVICE (зависит от Catalog + Elasticsearch)
# ═══════════════════════════════════════════════════════════

## T-801: Search — pyproject.toml + Dockerfile + .env.example
**Описание:** Базовые файлы
**Файлы:** `08-search-service/pyproject.toml`, `08-search-service/Dockerfile`, `08-search-service/.env.example`
**Переменные:** GRPC_PORT=50058, HTTP_PORT=8083, ES_HOSTS=http://elasticsearch:9200, ES_INDEX_NAME=products, DB_*, CATALOG_SERVICE_HOST=catalog-service, CATALOG_SERVICE_PORT=50051
**Важно:** HTTP_PORT=8083 — это ВНУТРЕННИЙ порт контейнера. На хосте маппинг **8087:8083** (совпадает с оригиналом, порт 8087 свободен)
**Критерий готовности:** Файлы созданы
**Зависимости:** T-003

## T-802: Search — config.py
**Описание:** Конфигурация
**Файл:** `08-search-service/src/config.py`
**Критерий готовности:** Settings загружается
**Зависимости:** T-801

## T-803: Search — Elasticsearch client
**Описание:** Клиент ES
**Файл:** `08-search-service/src/es_client/client.py`
**Методы:**
  - async def index_product(product_id, product_data)
  - async def search_products(query, filters, sort_by, sort_order, page, page_size)
  - async def suggest_products(query, limit)
  - async def reindex_catalog()
  - async def health_check()
**Критерий готовности:** Клиент соединяется с ES
**Зависимости:** T-802

## T-804: Search — gRPC клиенты
**Описание:** Клиент для Catalog Service
**Файл:** `08-search-service/src/grpc_client/catalog_client.py`
**Методы:** get_product(product_id), list_products()
**Критерий готовности:** Клиент работает
**Зависимости:** T-802

## T-805: Search — Services (бизнес-логика)
**Описание:** Сервисы
**Файл:** `08-search-service/src/services/search_service.py`
**Методы:**
  - async def search_products(query, category_ids, brand_ids, min_price, max_price, sort_by, sort_order, page, page_size)
  - async def suggest_products(query, limit)
  - async def index_product(product_id)
  - async def reindex_catalog()
**Критерий готовности:** Бизнес-логика реализована
**Зависимости:** T-803, T-804

## T-806: Search — gRPC server
**Описание:** Реализация gRPC service
**Файл:** `08-search-service/src/grpc_server/search_pb2_service.py`
**RPC:** SearchProducts, SuggestProducts, IndexProduct, ReindexCatalog
**Критерий готовности:** Все RPC работают
**Зависимости:** T-805

## T-807: Search — gRPC proto bindings
**Описание:** Генерация из search.proto
**Команда:** `python -m grpc_tools.protoc -I ../proto --python_out=. --grpc_python_out=. --pyi_out=. ../proto/search/v1/search.proto`
**Критерий готовности:** Файлы сгенерированы
**Зависимости:** T-806

## T-808: Search — HTTP API
**Описание:** REST-эндпоинты
**Файл:** `08-search-service/src/api/search.py`
**Эндпоинты:** GET /search/products, GET /search/suggest
**Критерий готовности:** Эндпоинты работают
**Зависимости:** T-805

## T-809: Search — main.py
**Описание:** Точка входа
**Файл:** `08-search-service/src/main.py`
**Критерий готовности:** Сервер запускается
**Зависимости:** T-806, T-807, T-808

## T-810: Search — Тесты
**Описание:** Unit-тесты
**Файлы:** `08-search-service/tests/test_search_service.py`
**Критерий готовности:** pytest проходит
**Зависимости:** T-805, T-809

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 9: NOTIFICATION SERVICE (зависит от Kafka + Order + Payment)
# ═══════════════════════════════════════════════════════════

## T-901: Notification — pyproject.toml + Dockerfile + .env.example
**Описание:** Базовые файлы
**Файлы:** `07-notification-service/pyproject.toml`, `07-notification-service/Dockerfile`, `07-notification-service/.env.example`
**Переменные:** GRPC_PORT=50057, HTTP_PORT=8086, DB_*, REDIS_DB=4, KAFKA_*, SMTP_*, PUSH_*, SMS_*, LOG_LEVEL=info, LOG_FORMAT=json
**Критерий готовности:** Файлы созданы
**Зависимости:** T-003

## T-902: Notification — config.py
**Описание:** Конфигурация
**Файл:** `07-notification-service/src/config.py`
**Критерий готовности:** Settings загружается
**Зависимости:** T-901

## T-903: Notification — SQLAlchemy модели
**Описание:** Модели БД
**Модели:**
  - Notification: id, user_id, type, channel, template, title, body, recipient, status, created_at, delivered_at, metadata (JSONB)
  - NotificationPreference: user_id, channel, enabled
**Критерий готовности:** Модели определены
**Зависимости:** T-902

## T-904: Notification — Database engine
**Описание:** Подключение к БД
**Файл:** `07-notification-service/src/database.py`
**Критерий готовности:** async_engine, get_db работают
**Зависимости:** T-902

## T-905: Notification — Kafka consumer
**Описание:** Потребление событий
**Файл:** `07-notification-service/src/kafka_consumer/consumer.py`
**Топики:** order.created, order.status_changed, payment.completed, payment.failed
**Методы:**
  - async def consume_order_created(order_data)
  - async def consume_order_status_changed(order_data)
  - async def consume_payment_completed(payment_data)
  - async def consume_payment_failed(payment_data)
**Критерий готовности:** Consumer подключается к Kafka
**Зависимости:** T-902

## T-906: Notification — Email sender
**Описание:** Отправка email
**Файл:** `07-notification-service/src/email/sender.py`
**Методы:**
  - async def send_order_confirmation(to_email, order_data)
  - async def send_order_status_update(to_email, order_data, new_status)
  - async def send_payment_confirmation(to_email, payment_data)
  - async def send_payment_failed(to_email, payment_data)
**Критерий готовности:** Email отправляется через SMTP
**Зависимости:** T-902

## T-907: Notification — Push/SMS senders
**Описание:** Отправка push и SMS
**Файлы:**
  - `src/push/sender.py`: send_push_notification(device_token, title, body)
  - `src/sms/sender.py`: send_sms(phone_number, message)
**Критерий готовности:** Методы определены (mock для prod)
**Зависимости:** T-902

## T-908: Notification — Repositories
**Описание:** Репозитории
**Файлы:**
  - `src/repositories/notification_repository.py`: create, get_by_user, list
  - `src/repositories/preference_repository.py`: get, update
**Критерий готовности:** CRUD-методы работают
**Зависимости:** T-903, T-904

## T-909: Notification — Services (бизнес-логика)
**Описание:** Сервисы
**Файл:** `07-notification-service/src/services/notification_service.py`
**Методы:**
  - async def send_notification(user_id, type, channel, template, data)
  - async def get_user_notifications(user_id, page, page_size, type)
  - async def update_preferences(user_id, channel, enabled)
  - async def handle_order_created(order_data)
  - async def handle_order_status_changed(order_data)
  - async def handle_payment_completed(payment_data)
  - async def handle_payment_failed(payment_data)
**Критерий готовности:** Бизнес-логика реализована
**Зависимости:** T-905, T-906, T-907, T-908

## T-910: Notification — gRPC server
**Описание:** Реализация gRPC service
**Файл:** `07-notification-service/src/grpc_server/notification_pb2_service.py`
**RPC:** SendNotification, GetUserNotifications, UpdateNotificationPreferences
**Критерий готовности:** Все RPC работают
**Зависимости:** T-909

## T-911: Notification — gRPC proto bindings
**Описание:** Генерация из notification.proto
**Команда:** `python -m grpc_tools.protoc -I ../proto --python_out=. --grpc_python_out=. --pyi_out=. ../proto/notification/v1/notification.proto`
**Критерий готовности:** Файлы сгенерированы
**Зависимости:** T-910

## T-912: Notification — HTTP API
**Описание:** REST-эндпоинты
**Файл:** `07-notification-service/src/api/notifications.py`
**Эндпоинты:** POST /notifications, GET /notifications, GET /notifications/preferences
**Критерий готовности:** Эндпоинты работают
**Зависимости:** T-909

## T-913: Notification — main.py
**Описание:** Точка входа
**Файл:** `07-notification-service/src/main.py`
**Критерий готовности:** Сервер запускается, Kafka consumer стартует
**Зависимости:** T-910, T-911, T-912

## T-914: Notification — Тесты
**Описание:** Unit-тесты
**Файлы:** `07-notification-service/tests/test_notification_service.py`
**Критерий готовности:** pytest проходит
**Зависимости:** T-909, T-913

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 10: SELLER SERVICE (зависит от Auth + Catalog + Order)
# ═══════════════════════════════════════════════════════════

## T-1001: Seller — pyproject.toml + Dockerfile + .env.example
**Описание:** Базовые файлы
**Файлы:** `09-seller-service/pyproject.toml`, `09-seller-service/Dockerfile`, `09-seller-service/.env.example`
**Переменные:** PORT=8085, GRPC_PORT=9090, HTTP_PORT=8085, ENV=production, DB_*, CATALOG_HOST=catalog-service, CATALOG_PORT=50051, ORDER_HOST=order-service, ORDER_PORT=50055, AUTH_HOST=auth-service, AUTH_PORT=50052
**Критерий готовности:** Файлы созданы
**Зависимости:** T-003

## T-1002: Seller — config.py
**Описание:** Конфигурация
**Файл:** `09-seller-service/src/config.py`
**Критерий готовности:** Settings загружается
**Зависимости:** T-1001

## T-1003: Seller — SQLAlchemy модели
**Описание:** Модели БД
**Модели:**
  - Seller: id, user_id, business_name, business_description, tax_id, logo_url, status, rating, total_ratings, total_sales, total_products, verification_doc_url, created_at, updated_at
  - SellerAccount: id, seller_id, bank_name, account_number, routing_number, account_holder_name, status, created_at, updated_at
  - SellerDocument: id, seller_id, type, file_url, status, verification_notes, created_at, updated_at
**Критерий готовности:** Модели определены
**Зависимости:** T-1002

## T-1004: Seller — Database engine
**Описание:** Подключение к БД
**Файл:** `09-seller-service/src/database.py`
**Критерий готовности:** async_engine, get_db работают
**Зависимости:** T-1002

## T-1005: Seller — gRPC клиенты
**Описание:** Клиенты для внешних сервисов
**Файлы:**
  - `src/grpc_client/auth_client.py`: verify_token
  - `src/grpc_client/catalog_client.py`: get_product, update_product_status
  - `src/grpc_client/order_client.py`: get_seller_orders, update_order_status
**Критерий готовности:** Клиенты работают
**Зависимости:** T-1002

## T-1006: Seller — Repositories
**Описание:** Репозитории
**Файлы:**
  - `src/repositories/seller_repository.py`: create, get_by_id, get_by_user, update, update_status, delete
  - `src/repositories/seller_account_repository.py`: create, get_by_seller, update
  - `src/repositories/seller_document_repository.py`: create, get_by_seller, get_by_id, update, verify
**Критерий готовности:** CRUD-методы работают
**Зависимости:** T-1003, T-1004

## T-1007: Seller — Services (бизнес-логика)
**Описание:** Сервисы
**Файл:** `09-seller-service/src/services/seller_service.py`
**Методы:**
  - register_seller, get_seller, get_seller_by_user, update_seller, update_seller_status, delete_seller
  - create_seller_account, get_seller_account, update_seller_account
  - upload_seller_document, get_seller_document, list_seller_documents, verify_seller_document
  - get_seller_products, update_product_status
  - get_seller_orders, update_order_status
  - get_seller_stats
**Критерий готовности:** Бизнес-логика реализована
**Зависимости:** T-1005, T-1006

## T-1008: Seller — gRPC server
**Описание:** Реализация gRPC service
**Файл:** `09-seller-service/src/grpc_server/seller_pb2_service.py`
**RPC:** RegisterSeller, GetSeller, GetSellerByUserId, UpdateSeller, UpdateSellerStatus, DeleteSeller, CreateSellerAccount, GetSellerAccount, UpdateSellerAccount, UploadSellerDocument, GetSellerDocument, ListSellerDocuments, VerifySellerDocument, GetSellerProducts, UpdateProductStatus, GetSellerOrders, UpdateOrderStatus, GetSellerStats
**Критерий готовности:** Все RPC работают
**Зависимости:** T-1007

## T-1009: Seller — gRPC proto bindings
**Описание:** Генерация из seller.proto
**Команда:** `python -m grpc_tools.protoc -I ../proto --python_out=. --grpc_python_out=. --pyi_out=. ../proto/seller/v1/seller.proto`
**Критерий готовности:** Файлы сгенерированы
**Зависимости:** T-1008

## T-1010: Seller — HTTP API
**Описание:** REST-эндпоинты
**Файл:** `09-seller-service/src/api/sellers.py`
**Эндпоинты:** POST /sellers/register, GET /sellers/{id}, PUT /sellers/{id}, GET /sellers/{id}/products, GET /sellers/{id}/orders, GET /sellers/{id}/stats
**Критерий готовности:** Эндпоинты работают
**Зависимости:** T-1007

## T-1011: Seller — main.py
**Описание:** Точка входа
**Файл:** `09-seller-service/src/main.py`
**Критерий готовности:** Сервер запускается
**Зависимости:** T-1008, T-1009, T-1010

## T-1012: Seller — Тесты
**Описание:** Unit-тесты
**Файлы:** `09-seller-service/tests/test_seller_service.py`
**Критерий готовности:** pytest проходит
**Зависимости:** T-1007, T-1011

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 11: ADMIN SERVICE (зависит от Auth)
# ═══════════════════════════════════════════════════════════

## T-1101: Admin — pyproject.toml + Dockerfile + .env.example
**Описание:** Базовые файлы
**Файлы:** `10-admin-service/pyproject.toml`, `10-admin-service/Dockerfile`, `10-admin-service/.env.example`
**Переменные:** PORT=8085, DB_*, AUTH_SERVICE_HOST=auth-service, AUTH_SERVICE_PORT=50052
**Критерий готовности:** Файлы созданы
**Зависимости:** T-003

## T-1102: Admin — config.py
**Описание:** Конфигурация
**Файл:** `10-admin-service/src/config.py`
**Критерий готовности:** Settings загружается
**Зависимости:** T-1101

## T-1103: Admin — gRPC клиент для Auth
**Описание:** Клиент для Auth Service
**Файл:** `10-admin-service/src/grpc_client/auth_client.py`
**Методы:** verify_token, get_user_from_token
**Критерий готовности:** Клиент работает
**Зависимости:** T-1102

## T-1104: Admin — Repositories
**Описание:** Репозитории
**Файлы:**
  - `src/repositories/admin_repository.py`: get_users, get_sellers, get_products, get_orders, get_payments
**Критерий готовности:** CRUD-методы работают
**Зависимости:** T-1102

## T-1105: Admin — Services (бизнес-логика)
**Описание:** Сервисы
**Файл:** `10-admin-service/src/services/admin_service.py`
**Методы:**
  - get_users(page, page_size)
  - get_sellers(page, page_size)
  - get_products(page, page_size)
  - get_orders(page, page_size, status)
  - get_payments(page, page_size, status)
  - update_user_role(user_id, role)
  - update_seller_status(seller_id, status)
  - update_product_status(product_id, status)
**Критерий готовности:** Бизнес-логика реализована
**Зависимости:** T-1103, T-1104

## T-1106: Admin — HTTP API
**Описание:** REST-эндпоинты
**Файл:** `10-admin-service/src/api/admin.py`
**Эндпоинты:** GET /admin/users, GET /admin/sellers, GET /admin/products, GET /admin/orders, GET /admin/payments, PUT /admin/users/{id}/role, PUT /admin/sellers/{id}/status
**Критерий готовности:** Эндпоинты работают
**Зависимости:** T-1105

## T-1107: Admin — main.py
**Описание:** Точка входа
**Файл:** `10-admin-service/src/main.py`
**Критерий готовности:** Сервер запускается
**Зависимости:** T-1106

## T-1108: Admin — Тесты
**Описание:** Unit-тесты
**Файлы:** `10-admin-service/tests/test_admin_service.py`
**Критерий готовности:** pytest проходит
**Зависимости:** T-1105, T-1107

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 12: BFF SERVICE (зависит от всех сервисов)
# ═══════════════════════════════════════════════════════════

## T-1201: BFF — pyproject.toml + Dockerfile + .env.example
**Описание:** Базовые файлы
**Файлы:** `11-bff-service/pyproject.toml`, `11-bff-service/Dockerfile`, `11-bff-service/.env.example`
**Переменные:** SERVER_PORT=8085, REDIS_*, JWT_*, CORS_*, RATE_LIMIT_*, HOST/PORT для всех сервисов
**Критерий готовности:** Файлы созданы
**Зависимости:** T-003

## T-1202: BFF — config.py
**Описание:** Конфигурация
**Файл:** `11-bff-service/src/config.py`
**Критерий готовности:** Settings загружается
**Зависимости:** T-1201

## T-1203: BFF — gRPC клиенты
**Описание:** Клиенты для всех сервисов
**Файлы:**
  - `src/grpc_client/catalog_client.py`: list_products, get_product
  - `src/grpc_client/auth_client.py`: verify_token
  - `src/grpc_client/cart_client.py`: get_cart
  - `src/grpc_client/order_client.py`: get_user_orders
  - `src/grpc_client/payment_client.py`: get_user_payments
  - `src/grpc_client/user_client.py`: get_user
  - `src/grpc_client/seller_client.py`: get_seller
  - `src/grpc_client/search_client.py`: search_products
  - `src/grpc_client/notification_client.py`: get_user_notifications
**Критерий готовности:** Все клиенты работают
**Зависимости:** T-1202

## T-1204: BFF — Services (агрегация)
**Описание:** Сервисы агрегации
**Файл:** `11-bff-service/src/services/bff_service.py`
**Методы:**
  - async def get_product_catalog(query, category, brand, min_price, max_price, sort, page, page_size)
  - async def get_product_details(product_id)
  - async def get_cart_with_prices(user_id)
  - async def checkout(user_id, cart_id, shipping_address, payment_method)
  - async def get_order_history(user_id, page, page_size, status)
  - async def get_user_profile(user_id)
  - async def get_seller_profile(seller_id, page, page_size)
  - async def get_user_notifications(user_id, page, page_size, unread_only)
**Критерий готовности:** Бизнес-логика реализована
**Зависимости:** T-1203

## T-1205: BFF — HTTP API
**Описание:** REST-эндпоинты
**Файл:** `11-bff-service/src/api/bff.py`
**Эндпоинты:**
  - GET /bff/products (catalog)
  - GET /bff/products/{id} (details)
  - GET /bff/cart (cart with prices)
  - POST /bff/checkout
  - GET /bff/orders (history)
  - GET /bff/user/profile
  - GET /bff/sellers/{id}
  - GET /bff/notifications
**Критерий готовности:** Эндпоинты работают
**Зависимости:** T-1204

## T-1206: BFF — Middleware
**Описание:** JWT middleware, CORS, Rate limiting
**Файл:** `11-bff-service/src/middleware/`
**Содержимое:**
  - jwt_auth.py: валидация JWT токена
  - cors.py: настройка CORS
  - rate_limit.py: slowapi rate limiting
**Критерий готовности:** Middleware работают
**Зависимости:** T-1202

## T-1207: BFF — main.py
**Описание:** Точка входа
**Файл:** `11-bff-service/src/main.py`
**Критерий готовности:** Сервер запускается
**Зависимости:** T-1205, T-1206

## T-1208: BFF — Тесты
**Описание:** Unit-тесты
**Файлы:** `11-bff-service/tests/test_bff_service.py`
**Критерий готовности:** pytest проходит
**Зависимости:** T-1204, T-1207

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 13: GATEWAY (зависит от Auth)
# ═══════════════════════════════════════════════════════════

## T-1301: Gateway — pyproject.toml + Dockerfile + .env.example
**Описание:** Базовые файлы
**Файлы:** `12-gateway/pyproject.toml`, `12-gateway/Dockerfile`, `12-gateway/.env.example`
**Переменные:** SERVER_PORT=8080, AUTH_SERVICE_HOST=auth-service, AUTH_SERVICE_PORT=50052
**Критерий готовности:** Файлы созданы
**Зависимости:** T-003

## T-1302: Gateway — config.py
**Описание:** Конфигурация
**Файл:** `12-gateway/src/config.py`
**Критерий готовности:** Settings загружается
**Зависимости:** T-1301

## T-1303: Gateway — gRPC клиент для Auth
**Описание:** Клиент для Auth Service
**Файл:** `12-gateway/src/grpc_client/auth_client.py`
**Методы:** verify_token(token) -> bool
**Критерий готовности:** Клиент работает
**Зависимости:** T-1302

## T-1304: Gateway — Middleware
**Описание:** JWT validation middleware
**Файл:** `12-gateway/src/middleware/auth_middleware.py`
**Функции:**
  - async def authenticate(request, call_next): извлекает Bearer token, вызывает Auth Service, добавляет user info в headers
**Критерий готовности:** Middleware валидирует токены
**Зависимости:** T-1303

## T-1305: Gateway — Routes
**Описание:** Роутинг запросов к сервисам
**Файл:** `12-gateway/src/routes/`
**Файлы:**
  - `auth_routes.py`: POST /auth/register, POST /auth/login, POST /auth/refresh, POST /auth/logout
  - `proxy_routes.py`: проксирование к BFF
**Критерий готовности:** Роуты работают
**Зависимости:** T-1304

## T-1306: Gateway — main.py
**Описание:** Точка входа
**Файл:** `12-gateway/src/main.py`
**Критерий готовности:** Сервер запускается на порту 8080
**Зависимости:** T-1305

## T-1307: Gateway — Тесты
**Описание:** Unit-тесты
**Файлы:** `12-gateway/tests/test_gateway.py`
**Критерий готовности:** pytest проходит
**Зависимости:** T-1305, T-1306

---

# ═══════════════════════════════════════════════════════════
# ФАЗА 14: ФИНАЛИЗАЦИЯ
# ═══════════════════════════════════════════════════════════

## T-1401: Собрать unified-docker-compose.yml
**Описание:** Добавить все сервисы приложения в единый compose
**Файл:** `unified-docker-compose.yml`
**Добавить сервисы:** auth-service, user-service, catalog-service, cart-service, order-service, payment-service, notification-service, search-service, seller-service, admin-service, bff-service, gateway
**Критерий готовности:** docker compose config валиден
**Зависимости:** T-214, T-315, T-411, T-510, T-612, T-713, T-810, T-914, T-1012, T-1108, T-1208, T-1307

## T-1402: Запустить инфраструктуру
**Описание:** Поднять Docker-контейнеры
**Команды:**
  1. `cd C:\Users\andre\Desktop\project\migration_plan`
  2. `docker compose -f unified-docker-compose.yml up -d postgres redis elasticsearch zookeeper kafka`
  3. Подождать 30 секунд
  4. `docker compose -f unified-docker-compose.yml ps` — проверить status всех сервисов
**Важно:** PostgreSQL будет доступен на **15432** (не 5432) из-за конфликта с локальным PostgreSQL
**Критерий готовности:** Все инфраструктурные контейнеры в статусе healthy
**Зависимости:** T-1401

## T-1402.1: Проверка порта PostgreSQL
**Описание:** Убедиться что PostgreSQL запущен на новом порту
**Команды:**
  1. `docker compose -f unified-docker-compose.yml exec postgres pg_isready -U postgres -h localhost -p 5432`
  2. `netstat -ano | findstr ":15432"` — проверить маппинг
**Критерий готовности:** pg_isready отвечает, порт 15432 маппится на 5432
**Зависимости:** T-1402

## T-1402.2: Проверка порта Search Service
**Описание:** Убедиться что Search Service HTTP доступен на 8087
**Команды:**
  1. `docker compose -f unified-docker-compose.yml ps search-service` — проверить маппинг портов
  2. `netstat -ano | findstr ":8087"` — проверить маппинг
**Критерий готовности:** Порт 8087 маппится на 8083 контейнера
**Зависимости:** T-1402

## T-1403: Smoke-тесты
**Описание:** Проверить health-check всех сервисов
**Команды:**
  1. `curl http://localhost:8080/health` (Gateway)
  2. `curl http://localhost:8084/health` (Catalog)
  3. `curl http://localhost:8087/health` (Search HTTP — **8087**, не 8083!)
  4. `docker compose -f unified-docker-compose.yml logs --tail=50`
**Важно:** Search Service HTTP на **8087**, PostgreSQL на **15432**
**Критерий готовности:** Все health-check'и отвечают
**Зависимости:** T-1402

## T-1404: Документация запуска
**Описание:** Создать инструкцию по запуску
**Файл:** `RUN_INSTRUCTIONS.md`
**Содержимое:**
  1. Требования (Docker, Python 3.12+)
  2. Быстрый старт (docker compose up)
  3. Структура портов
  4. Переменные окружения
  5. Troubleshooting
**Критерий готовности:** Инструкция покрывает все шаги запуска
**Зависимости:** T-1403

---

# ═══════════════════════════════════════════════════════════
# ИТОГО: 144 АТОМАРНЫЕ ЗАДАЧИ
# ═══════════════════════════════════════════════════════════

| Фаза | Задачи | Кол-во | Оценка времени |
|---|---|---:|---:|
| 0. Подготовка | T-001 .. T-004 | 4 | 30 мин |
| 1. Инфраструктура | T-101 .. T-103 | 3 | 15 мин |
| 2. Auth Service | T-201 .. T-214 | 14 | 2-3 часа |
| 3. Catalog Service | T-301 .. T-315 | 15 | 2-3 часа |
| 4. User Service | T-401 .. T-411 | 11 | 1.5-2 часа |
| 5. Cart Service | T-501 .. T-510 | 10 | 1.5-2 часа |
| 6. Order Service | T-601 .. T-612 | 12 | 2-3 часа |
| 7. Payment Service | T-701 .. T-713 | 13 | 2-3 часа |
| 8. Search Service | T-801 .. T-810 | 10 | 1.5-2 часа |
| 9. Notification Service | T-901 .. T-914 | 14 | 2-3 часа |
| 10. Seller Service | T-1001 .. T-1012 | 12 | 2-3 часа |
| 11. Admin Service | T-1101 .. T-1108 | 8 | 1-1.5 часа |
| 12. BFF Service | T-1201 .. T-1208 | 8 | 1.5-2 часа |
| 13. Gateway | T-1301 .. T-1307 | 7 | 1-1.5 часа |
| 14. Финализация | T-1401 .. T-1404 | 4 | 30 мин |
| **ВСЕГО** | | **146** | **~25-35 часов** |

---

## 📋 ИТОГОВАЯ КАРТА ПОРТОВ (с исправлениями конфликтов)

### Инфраструктура

| Порт (хост) | Порт (контейнер) | Сервис | Статус |
|---|---|---|---|
| **15432** | 5432 | postgres | ⚠️ ИЗМЕНЁН (было 5432) |
| 6379 | 6379 | redis | OK |
| 9200 | 9200 | elasticsearch | OK |
| 5601 | 5601 | kibana | OK |
| 2181 | 2181 | zookeeper | OK |
| 9092 | 9092 | kafka | OK |
| 1025 | 1025 | mailhog | OK |
| 8025 | 8025 | mailhog | OK |
| 9090 | 9090 | prometheus | OK |
| 3000 | 3000 | grafana | OK |

### Сервисы приложения

| Порт (хост) | Порт (контейнер) | Сервис | Статус |
|---|---|---|---|
| 8080 | 8080 | gateway | OK |
| 50051 | 50052 | auth-service | OK |
| 50052 | 50053 | user-service | OK |
| 50053 | 50051 | catalog-service | OK |
| 50054 | 50050 | cart-service | OK |
| 50055 | 50055 | order-service | OK |
| 50056 | 50056 | payment-service | OK |
| 50057 | 50057 | notification-service | OK |
| 50058 | 50058 | search-service | OK |
| 8081 | 8081 | cart-service (HTTP) | OK |
| 8082 | 8082 | payment-service (HTTP) | OK |
| **18083** | 8083 | search-service (HTTP) | ⚠️ ИЗМЕНЁН (было 8083) |
| 8084 | 8080 | catalog-service (HTTP) | OK |
| 8085 | 8085 | bff-service | OK |
| 8086 | 8086 | notification-service (HTTP) | OK |
| 8087 | 8085 | admin-service | OK |
| 8088 | 8085 | seller-service | OK |
| 8089 | 8085 | bff-service (alt) | OK |
| 8090 | 9090 | seller-service (gRPC) | OK |

### Занятые порты на хосте (НЕ ИЗМЕНЯЕМ, пропускаем)

| Порт | Процесс | Решение |
|---|---|---|
| 5432 | postgres (PID 5936) | Использовать 15432 |
| 7680 | svchost (PID 17668) | Не использовать в плане |
| 8083 | System (PID 4) | Использовать 18083 |
