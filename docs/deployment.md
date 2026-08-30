# Deployment Guide

Comprehensive guide for deploying the HyperScale Marketplace to production environments.

---

## Table of Contents

- [Production Requirements](#production-requirements)
- [Environment Variables](#environment-variables)
- [Docker Compose Production Config](#docker-compose-production-config)
- [Kubernetes Manifests](#kubernetes-manifests)
- [SSL/TLS Setup](#ssltls-setup)
- [Backup Procedures](#backup-procedures)
- [Rolling Updates](#rolling-updates)
- [Disaster Recovery](#disaster-recovery)

---

## Production Requirements

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **PostgreSQL** | 2 vCPU, 4 GB RAM | 4 vCPU, 16 GB RAM |
| **Redis** | 1 vCPU, 1 GB RAM | 2 vCPU, 4 GB RAM |
| **Elasticsearch** | 2 vCPU, 4 GB RAM | 4 vCPU, 16 GB RAM |
| **Kafka** | 2 vCPU, 4 GB RAM | 4 vCPU, 8 GB RAM |
| **App Services** | 0.5 vCPU, 256 MB RAM | 1 vCPU, 512 MB RAM |
| **Prometheus** | 1 vCPU, 2 GB RAM | 2 vCPU, 8 GB RAM |
| **Grafana** | 0.5 vCPU, 512 MB RAM | 1 vCPU, 2 GB RAM |

### Software Requirements

| Component | Version |
|-----------|---------|
| Docker | 24.0+ |
| Docker Compose | 2.20+ |
| Kubernetes | 1.28+ (if using K8s) |
| TLS | 1.3 (preferred), 1.2 (fallback) |
| Database backups | Automated, 30-day retention |

### Security Requirements

- TLS/SSL for all external endpoints
- Secrets management (Vault, AWS Secrets Manager, etc.)
- Network segmentation between services
- Regular security audits
- Dependency vulnerability scanning

---

## Environment Variables

### Production .env Template

```bash
# ============================================================
# HyperScale Marketplace — Production Environment Variables
# ============================================================

# ── Application ─────────────────────────────────────────────
APP_ENV=production
DEBUG=0
LOG_LEVEL=info
LOG_FORMAT=json

# ── Database ────────────────────────────────────────────────
DB_HOST=<db-host>
DB_PORT=5432
DB_USER=<db-user>
DB_PASSWORD=<strong-password>
DB_SSL_MODE=require
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Per-service databases
DB_AUTH_NAME=auth_db
DB_USER_SERVICE_NAME=user_db
DB_CATALOG_NAME=catalog_db
DB_CART_NAME=cart_db
DB_ORDER_NAME=order_db
DB_PAYMENT_NAME=payment_db
DB_NOTIFICATION_NAME=notification_db
DB_SEARCH_NAME=search_db
DB_SELLER_NAME=seller_db
DB_ADMIN_NAME=admin_db

# ── Redis ───────────────────────────────────────────────────
REDIS_HOST=<redis-host>
REDIS_PORT=6379
REDIS_PASSWORD=<redis-password>
REDIS_MAX_CONNECTIONS=50

# ── Elasticsearch ──────────────────────────────────────────
ES_HOSTS=https://<es-host>:9200
ES_INDEX_NAME=products
ES_USERNAME=<es-user>
ES_PASSWORD=<es-password>
ES_SNIFF=true
ES_HEALTHCHECK_ENABLED=true

# ── Kafka ──────────────────────────────────────────────────
KAFKA_BROKERS=<kafka-host>:9092
KAFKA_GROUP_ID=marketplace-prod-group
KAFKA_AUTO_OFFSET_RESET=earliest
KAFKA_MAX_RETRIES=5

# ── JWT ────────────────────────────────────────────────────
JWT_SECRET=<strong-random-64-char-string>
JWT_EXPIRY=3600
JWT_ISSUER=auth-service
JWT_ALGORITHM=HS256
BCRYPT_ROUNDS=12

# ── Gateway / BFF ─────────────────────────────────────────
CORS_ALLOWED_ORIGINS=https://app.marketplace.com,https://admin.marketplace.com
RATE_LIMIT_RPS=200
RATE_LIMIT_BURST=400
BFF_REDIS_PREFIX=bff:

# ── Payment ────────────────────────────────────────────────
STRIPE_SECRET_KEY=<stripe-secret-key>
STRIPE_WEBHOOK_SECRET=<stripe-webhook-secret>
STRIPE_PUBLISHABLE_KEY=<stripe-publishable-key>
YOOMONEY_SHOP_ID=<yoomoney-shop-id>
YOOMONEY_TOKEN=<yoomoney-token>
PAYMENT_CURRENCY=RUB
PAYMENT_TIMEOUT=1800

# ── Notification ───────────────────────────────────────────
SMTP_HOST=<smtp-host>
SMTP_PORT=587
SMTP_USERNAME=<smtp-user>
SMTP_PASSWORD=<smtp-password>
SMTP_FROM_EMAIL=noreply@marketplace.com
SMTP_ENABLE_TLS=true
PUSH_PROVIDER=firebase
PUSH_ENABLED=true
PUSH_API_KEY=<firebase-api-key>
PUSH_PROJECT_ID=<firebase-project-id>
SMS_PROVIDER=twilio
SMS_ENABLED=true
SMS_ACCOUNT_SID=<twilio-sid>
SMS_AUTH_TOKEN=<twilio-token>
SMS_FROM_NUMBER=<twilio-phone>

# ── Monitoring ─────────────────────────────────────────────
PROMETHEUS_ENDPOINT=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=<grafana-admin-password>

# ── Domain ─────────────────────────────────────────────────
GATEWAY_URL=https://api.marketplace.com
AUTH_SERVICE_URL=https://auth.marketplace.com
CATALOG_SERVICE_URL=https://catalog.marketplace.com
ORDER_SERVICE_URL=https://order.marketplace.com
PAYMENT_SERVICE_URL=https://payment.marketplace.com

# ── Feature Flags ──────────────────────────────────────────
ENABLE_KAFKA_INTEGRATION=true
ENABLE_REDIS_CACHE=true
ENABLE_PROMETHEUS_METRICS=true
ENABLE_RATE_LIMITING=true
ENABLE_CORS=true
ENABLE_SWAGGER=false
```

---

## Docker Compose Production Config

### Production Override (`docker-compose.prod.yml`)

```yaml
version: '3.8'

# Production overrides for all services
x-service-defaults: &service-defaults
  restart: always
  deploy:
    resources:
      limits:
        memory: 512M
        cpus: '1.0'
      reservations:
        memory: 256M
        cpus: '0.5'
    rollback_config:
      parallelism: 1
      delay: 10s
    update_config:
      parallelism: 1
      delay: 10s
      order: stop-first

# Override infrastructure with production settings
services:
  postgres:
    environment:
      POSTGRES_INITDB_ARGS: --encoding=UTF-8 --locale=en_US.UTF-8
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./00-infrastructure/postgres/init-db:/docker-entrypoint-initdb.d
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
        reservations:
          memory: 1G
          cpus: '1.0'

  redis:
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 512mb --maxmemory-policy allkeys-lru
    deploy:
      resources:
        limits:
          memory: 512M

  elasticsearch:
    environment:
      discovery.type: single-node
      ES_JAVA_OPTS: -Xms1g -Xmx1g
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    deploy:
      resources:
        limits:
          memory: 2G

  kafka:
    environment:
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
    deploy:
      resources:
        limits:
          memory: 1G

  # Application services use defaults
  auth-service:
    <<: *service-defaults
    environment:
      - DB_SSL_MODE=require
      - LOG_LEVEL=${LOG_LEVEL}

  catalog-service:
    <<: *service-defaults

  order-service:
    <<: *service-defaults

  payment-service:
    <<: *service-defaults
    environment:
      - DB_SSL_MODE=require

  bff-service:
    <<: *service-defaults

  gateway:
    <<: *service-defaults
    ports:
      - "443:8080"  # HTTPS
      - "8080:8080" # HTTP (redirect to HTTPS)

volumes:
  postgres-data:
    driver: local
  redis-data:
    driver: local
  elasticsearch-data:
    driver: local
  prometheus-data:
    driver: local
  grafana-data:
    driver: local
```

### Deploy with Production Config

```bash
# Start with production overrides
docker compose -f unified-docker-compose.yml -f docker-compose.prod.yml --profile all up -d

# Or use the Makefile with prod profile
make up PROFILE=infra
```

---

## Kubernetes Manifests

### Namespace

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: marketplace
```

### PostgreSQL Deployment

```yaml
# k8s/postgres.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: marketplace
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16-alpine
          env:
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: marketplace-secrets
                  key: db-user
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: marketplace-secrets
                  key: db-password
            - name: POSTGRES_DB
              value: marketplace
          ports:
            - containerPort: 5432
          resources:
            limits:
              memory: "2Gi"
              cpu: "2000m"
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
      volumes:
        - name: postgres-data
          persistentVolumeClaim:
            claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: marketplace
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
```

### Service Deployment Template

```yaml
# k8s/service-template.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{SERVICE_NAME}}
  namespace: marketplace
spec:
  replicas: {{REPLICAS}}
  selector:
    matchLabels:
      app: {{SERVICE_NAME}}
  template:
    metadata:
      labels:
        app: {{SERVICE_NAME}}
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "{{HTTP_PORT}}"
    spec:
      containers:
        - name: {{SERVICE_NAME}}
          image: {{IMAGE}}:{{TAG}}
          ports:
            - containerPort: {{HTTP_PORT}}
            - containerPort: {{GRPC_PORT}}
          env:
            - name: DB_HOST
              value: postgres.marketplace.svc.cluster.local
            - name: DB_PORT
              value: "5432"
            - name: DB_USER
              valueFrom:
                secretKeyRef:
                  name: marketplace-secrets
                  key: db-user
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: marketplace-secrets
                  key: db-password
            - name: REDIS_HOST
              value: redis.marketplace.svc.cluster.local
            - name: LOG_LEVEL
              value: info
          resources:
            limits:
              memory: "512Mi"
              cpu: "500m"
            requests:
              memory: "256Mi"
              cpu: "250m"
          readinessProbe:
            httpGet:
              path: /health
              port: {{HTTP_PORT}}
            initialDelaySeconds: 10
            periodSeconds: 15
          livenessProbe:
            httpGet:
              path: /health
              port: {{HTTP_PORT}}
            initialDelaySeconds: 30
            periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: {{SERVICE_NAME}}
  namespace: marketplace
spec:
  selector:
    app: {{SERVICE_NAME}}
  ports:
    - name: http
      port: {{HTTP_PORT}}
      targetPort: {{HTTP_PORT}}
    - name: grpc
      port: {{GRPC_PORT}}
      targetPort: {{GRPC_PORT}}
```

### Gateway Deployment

```yaml
# k8s/gateway.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway
  namespace: marketplace
spec:
  replicas: 2
  selector:
    matchLabels:
      app: gateway
  template:
    metadata:
      labels:
        app: gateway
    spec:
      containers:
        - name: gateway
          image: marketplace/gateway:latest
          ports:
            - containerPort: 8080
          env:
            - name: SERVER_PORT
              value: "8080"
            - name: LOG_LEVEL
              value: info
          resources:
            limits:
              memory: "512Mi"
              cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: gateway
  namespace: marketplace
spec:
  type: LoadBalancer
  selector:
    app: gateway
  ports:
    - name: http
      port: 80
      targetPort: 8080
    - name: https
      port: 443
      targetPort: 8080
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: marketplace-ingress
  namespace: marketplace
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "60s"
spec:
  tls:
    - hosts:
        - api.marketplace.com
      secretName: marketplace-tls
  rules:
    - host: api.marketplace.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: gateway
                port:
                  number: 80
```

### Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Apply all manifests
kubectl apply -f k8s/

# Or apply with kustomize
kubectl apply -k k8s/

# Check deployment
kubectl get all -n marketplace

# View logs
kubectl logs -f deployment/gateway -n marketplace
```

---

## SSL/TLS Setup

### Option 1: Let's Encrypt (Recommended for Production)

```bash
# Install certbot
apt-get install certbot

# Generate certificates
certbot certonly --standalone -d api.marketplace.com \
  -d app.marketplace.com \
  --email admin@marketplace.com \
  --agree-tos

# Copy certificates
cp /etc/letsencrypt/live/api.marketplace.com/fullchain.pem /etc/ssl/certs/marketplace.crt
cp /etc/letsencrypt/live/api.marketplace.com/privkey.pem /etc/ssl/private/marketplace.key

# Set permissions
chmod 644 /etc/ssl/certs/marketplace.crt
chmod 600 /etc/ssl/private/marketplace.key
```

### Option 2: Self-Signed (Development/Staging)

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout marketplace.key \
  -out marketplace.crt -days 365 -nodes \
  -subj "/CN=marketplace.local" \
  -addext "subjectAltName=DNS:marketplace.local,DNS:*.marketplace.local"
```

### Option 3: Kubernetes TLS Secrets

```bash
# Create TLS secret
kubectl create secret tls marketplace-tls \
  --cert=/etc/letsencrypt/live/api.marketplace.com/fullchain.pem \
  --key=/etc/letsencrypt/live/api.marketplace.com/privkey.pem \
  -n marketplace

# Or create from existing cert files
kubectl create secret tls marketplace-tls \
  --cert=marketplace.crt \
  --key=marketplace.key \
  -n marketplace
```

### TLS Configuration

```yaml
# docker-compose.prod.yml
services:
  gateway:
    environment:
      - TLS_CERT_PATH=/etc/ssl/certs/marketplace.crt
      - TLS_KEY_PATH=/etc/ssl/private/marketplace.key
      - TLS_CA_PATH=/etc/ssl/certs/ca-certificates.crt
    volumes:
      - /etc/letsencrypt/live/api.marketplace.com:/etc/ssl/certs:ro
      - /etc/letsencrypt/live/api.marketplace.com:/etc/ssl/private:ro
```

---

## Backup Procedures

### PostgreSQL Backups

```bash
# Manual backup
docker exec marketplace-postgres pg_dump -U postgres auth_db > backups/auth_db_$(date +%Y%m%d).sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)

for DB in auth_db user_db catalog_db cart_db order_db payment_db notification_db search_db seller_db admin_db; do
  docker exec marketplace-postgres pg_dump -U postgres $DB | gzip > ${BACKUP_DIR}/${DB}_${DATE}.sql.gz
done

# Retention: keep last 30 days
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +30 -delete
```

### Redis Backups

```bash
# Trigger RDB snapshot
docker exec marketplace-redis redis-cli SAVE

# Copy RDB file
docker cp marketplace-redis:/data/dump.rdb ./backups/redis_dump_$(date +%Y%m%d).rdb
```

### Elasticsearch Snapshots

```bash
# Register snapshot repository
curl -X PUT "localhost:9200/_snapshot/marketplace_backup" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "fs",
    "settings": {
      "location": "/mnt/backups/elasticsearch",
      "compress": true
    }
  }'

# Create snapshot
curl -X PUT "localhost:9200/_snapshot/marketplace_backup/snapshot_$(date +%Y%m%d)?wait_for_completion=true"

# List snapshots
curl "localhost:9200/_snapshot/marketplace_backup/_all"
```

### Backup Schedule (Cron)

```bash
# Add to crontab
0 2 * * * /opt/marketplace/scripts/backup-postgres.sh
0 3 * * * /opt/marketplace/scripts/backup-redis.sh
0 4 * * * /opt/marketplace/scripts/backup-elasticsearch.sh
```

---

## Rolling Updates

### Update Services

```bash
# Update a single service
docker compose --profile services up -d --no-deps --build auth-service

# Update all services
docker compose --profile services up -d --no-deps --build

# Kubernetes rolling update
kubectl rollout restart deployment/auth-service -n marketplace
kubectl rollout status deployment/auth-service -n marketplace
```

### Health Check Before Restart

```bash
# Check service health before update
make health

# Or individually
curl -s http://localhost:8080/health | jq
```

---

## Disaster Recovery

### Recovery Procedures

| Scenario | Recovery Steps |
|----------|---------------|
| **PostgreSQL failure** | Restore from latest backup, point services to new DB |
| **Redis failure** | Restart Redis; data will be rebuilt from DB |
| **Kafka failure** | Restart Kafka + Zookeeper; consumers will reconnect |
| **Elasticsearch failure** | Restore from snapshot; reindex if needed |
| **Full cluster failure** | Restore from off-site backups; redeploy infrastructure |

### RTO/RPO Targets

| Component | RTO | RPO |
|-----------|-----|-----|
| PostgreSQL | 15 min | 1 hour |
| Redis | 5 min | None (cache) |
| Kafka | 10 min | None (persistent) |
| Elasticsearch | 30 min | 1 hour |
| App Services | 5 min | None (stateless) |

---

## Related Documentation

- [Main README](../README.md) — Project overview
- [Monitoring](monitoring.md) — Observability setup
- [Development Guide](development.md) — Local development
