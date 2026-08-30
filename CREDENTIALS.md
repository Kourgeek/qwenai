# HyperScale Marketplace — Файл учетных данных

## 🔐 Админские учетные записи

### Auth Service (основная)
| Поле | Значение |
|------|----------|
| **Email** | `admin@marketplace.local` |
| **Password** | `Adm1n@2026!` |
| **Role** | admin |

> **Примечание:** Пароль `Admin@12345` отклонён политикой паролей (содержит последовательные символы "12345"). Использован валидный пароль `Adm1n@2026!`.

### PostgreSQL
| Поле | Значение |
|------|----------|
| **Host** | `localhost:15432` |
| **User** | `postgres` |
| **Password** | `postgres` |
| **Database** | `marketplace` (основная), `auth_db`, `catalog_db`, `user_db`, `cart_db`, `order_db`, `payment_db`, `notification_db`, `search_db`, `seller_db`, `admin_db` |

### Redis
| Поле | Значение |
|------|----------|
| **Host** | `localhost:6379` |
| **Password** | (пустой) |

### Elasticsearch
| Поле | Значение |
|------|----------|
| **URL** | `http://localhost:9200` |
| **User** | (security отключен) |
| **Password** | (пустой) |

### Kibana
| Поле | Значение |
|------|----------|
| **URL** | `http://localhost:5601` |
| **User** | `elastic` |
| **Password** | (см. логи контейнера) |

### Prometheus
| Поле | Значение |
|------|----------|
| **URL** | `http://localhost:9090` |
| **User** | (пустой) |
| **Password** | (пустой) |

### Grafana
| Поле | Значение |
|------|----------|
| **URL** | `http://localhost:3000` |
| **User** | `admin` |
| **Password** | `admin` |

### MailHog
| Поле | Значение |
|------|----------|
| **URL** | `http://localhost:8025` |
| **SMTP** | `localhost:1025` |

---

## 🌐 Ссылки на UI (port 3001)

| Страница | URL |
|----------|-----|
| **Главная** | http://localhost:3001/ |
| **Товары** | http://localhost:3001/products |
| **Корзина** | http://localhost:3001/cart |
| **Вход** | http://localhost:3001/login |
| **Регистрация** | http://localhost:3001/register |
| **Профиль** | http://localhost:3001/profile |
| **Seller Dashboard** | http://localhost:3001/seller |
| **Admin Dashboard** | http://localhost:3001/admin |

---

## 🔧 API Gateway

| Сервис | URL |
|--------|-----|
| **Health** | http://localhost:8080/health |
| **Swagger** | http://localhost:8080/docs |
| **ReDoc** | http://localhost:8080/redoc |

---

## 📦 Приложения

| Сервис | Health | Swagger |
|--------|--------|---------|
| auth-service | http://localhost:50051/health | — |
| user-service | http://localhost:50052/health | — |
| catalog-service | http://localhost:8084/health | http://localhost:8084/docs |
| cart-service | http://localhost:8081/health | — |
| order-service | http://localhost:50055/health | — |
| payment-service | http://localhost:8082/health | — |
| notification-service | http://localhost:8086/health | — |
| search-service | http://localhost:8087/health | — |
| seller-service | http://localhost:8090/health | — |
| admin-service | http://localhost:8088/health | — |
| bff-service | http://localhost:8089/health | http://localhost:8089/docs |

---

## 🗄️ Инфраструктура

| Сервис | URL |
|--------|-----|
| PostgreSQL | localhost:15432 |
| Redis | localhost:6379 |
| Elasticsearch | http://localhost:9200 |
| Kibana | http://localhost:5601 |
| Kafka | localhost:9092 |
| Zookeeper | localhost:2181 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |
| MailHog | http://localhost:8025 |

---

## ⚡ Полезные команды

```powershell
# Запуск всех сервисов
cd C:\Users\andre\Desktop\project\migration_plan
docker compose -f unified-docker-compose.yml up -d

# Запуск UI
cd ui
npm run dev

# Проверка здоровья
docker compose -f unified-docker-compose.yml ps

# Логи конкретного сервиса
docker compose -f unified-docker-compose.yml logs -f <service-name>

# Остановка всех сервисов
docker compose -f unified-docker-compose.yml down

# Перезапуск
docker compose -f unified-docker-compose.yml restart
```

---

## 📝 Примечания

1. **Пароль по умолчанию**: `Admin@12345` для всех админских аккаунтов
2. **JWT Secret**: `change-me-in-production` (указать в .env)
3. **BFF JWT Secret**: `bff-secret-key-change-in-production`
4. **Stripe Test Key**: `sk_test_placeholder` (заменить на реальный)
5. **YooMoney**: Shop ID и Token нужно заполнить в .env
6. **Firebase Push**: Push_ENABLED=false по умолчанию
7. **Twilio SMS**: SMS_ENABLED=false по умолчанию

---

**Создано**: 2026-08-03
**Статус**: Все сервисы healthy
