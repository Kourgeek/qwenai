# Monitoring Documentation

Comprehensive guide for monitoring the HyperScale Marketplace using Prometheus, Grafana, and related tools.

---

## Table of Contents

- [Monitoring Architecture](#monitoring-architecture)
- [Prometheus Setup](#prometheus-setup)
- [Grafana Dashboards](#grafana-dashboards)
- [Alerting Rules](#alerting-rules)
- [Log Aggregation](#log-aggregation)
- [Distributed Tracing](#distributed-tracing)
- [Custom Metrics](#custom-metrics)

---

## Monitoring Architecture

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Auth        │    │  Catalog     │    │  Order       │
│  Service     │    │  Service     │    │  Service     │
│  :9090/metrics│   │  :9090/metrics│   │  :9090/metrics│
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌──────────────────────────────────────────────────────────┐
│                    Prometheus                             │
│                    :9090                                │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Scraping: HTTP /metrics endpoints                │  │
│  │  Storage: TSDB (time-series)                      │  │
│  │  Query: PromQL                                    │  │
│  └────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│                     Grafana                              │
│                     :3000                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Service      │  │ Infrastructure│  │ Business     │   │
│  │ Health       │  │ Resources     │  │ Metrics      │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │ Error Rate   │  │ Latency      │                     │
│  └──────────────┘  └──────────────┘                     │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│                   Alertmanager                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Email    │  │ Slack    │  │ PagerDuty│              │
│  └──────────┘  └──────────┘  └──────────┘              │
└──────────────────────────────────────────────────────────┘
```

---

## Prometheus Setup

### Configuration (`prometheus.yml`)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - '/etc/prometheus/rules/*.yml'

scrape_configs:
  # Gateway
  - job_name: 'gateway'
    static_configs:
      - targets: ['gateway:8080']
    metrics_path: '/metrics'

  # Auth Service
  - job_name: 'auth-service'
    static_configs:
      - targets: ['auth-service:50052']
    metrics_path: '/metrics'

  # Catalog Service
  - job_name: 'catalog-service'
    static_configs:
      - targets: ['catalog-service:8080']
    metrics_path: '/metrics'

  # Cart Service
  - job_name: 'cart-service'
    static_configs:
      - targets: ['cart-service:8081']
    metrics_path: '/metrics'

  # Order Service
  - job_name: 'order-service'
    static_configs:
      - targets: ['order-service:8085']
    metrics_path: '/metrics'

  # Payment Service
  - job_name: 'payment-service'
    static_configs:
      - targets: ['payment-service:8082']
    metrics_path: '/metrics'

  # Notification Service
  - job_name: 'notification-service'
    static_configs:
      - targets: ['notification-service:8086']
    metrics_path: '/metrics'

  # Search Service
  - job_name: 'search-service'
    static_configs:
      - targets: ['search-service:8083']
    metrics_path: '/metrics'

  # Seller Service
  - job_name: 'seller-service'
    static_configs:
      - targets: ['seller-service:8085']
    metrics_path: '/metrics'

  # Admin Service
  - job_name: 'admin-service'
    static_configs:
      - targets: ['admin-service:8085']
    metrics_path: '/metrics'

  # BFF Service
  - job_name: 'bff-service'
    static_configs:
      - targets: ['bff-service:8085']
    metrics_path: '/metrics'

  # Infrastructure
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:9187']
    metrics_path: '/metrics'

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:9121']
    metrics_path: '/metrics'

  - job_name: 'elasticsearch'
    static_configs:
      - targets: ['elasticsearch:9400']
    metrics_path: '/metrics'

  - job_name: 'kafka'
    static_configs:
      - targets: ['kafka:9308']
    metrics_path: '/metrics'
```

### Prometheus Rules

```yaml
# rules/alerts.yml
groups:
  - name: service_alerts
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on {{ $labels.service }}"
          description: "Error rate is {{ $value | humanizePercentage }} on {{ $labels.service }}"

      # High latency
      - alert: HighLatency
        expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency on {{ $labels.service }}"
          description: "99th percentile latency is {{ $value }}s on {{ $labels.service }}"

      # Service down
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "Service {{ $labels.job }} has been down for more than 1 minute"

  - name: infrastructure_alerts
    rules:
      # High memory usage
      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes / 1024 / 1024 > 400
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory on {{ $labels.job }}"
          description: "{{ $value }} MB memory usage on {{ $labels.job }}"

      # Disk usage
      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Disk space low on {{ $labels.instance }}"
          description: "Less than 10% disk space remaining on {{ $labels.instance }}"
```

---

## Grafana Dashboards

### Dashboard: Service Health Overview

**Purpose:** Monitor all services' health, request rates, and error rates.

**Panels:**

| Panel | Type | Query |
|-------|------|-------|
| Request Rate | Time Series | `rate(http_requests_total[5m])` |
| Error Rate | Time Series | `rate(http_requests_total{status=~"5.."}[5m])` |
| p99 Latency | Time Series | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` |
| p50 Latency | Time Series | `histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))` |
| Active Connections | Gauge | `http_connections_active` |
| Service Health | Status History | `up` |

### Dashboard: Infrastructure Health

**Purpose:** Monitor PostgreSQL, Redis, Elasticsearch, and Kafka.

| Panel | Type | Query |
|-------|------|-------|
| DB Connection Pool | Gauge | `pg_stat_activity_count` |
| DB Queries/sec | Time Series | `rate(pg_stat_database_xact_commit[5m])` |
| Redis Memory | Gauge | `redis_memory_used_bytes` |
| Redis Hit Rate | Gauge | `rate(redis_keyspace_hits_total[5m]) / rate(redis_keyspace_hits_total[5m] + redis_keyspace_misses_total[5m])` |
| ES Heap | Gauge | `jvm_memory_used_bytes{area="heap"}` |
| ES Index Size | Gauge | `elasticsearch_indices_store_size_bytes` |
| Kafka Consumer Lag | Gauge | `kafka_consumer_group_lag` |

### Dashboard: Business Metrics

**Purpose:** Track marketplace business KPIs.

| Panel | Type | Description |
|-------|------|-------------|
| Orders/hour | Time Series | `rate(orders_created_total[1h])` |
| Revenue | Time Series | `rate(payment_amount_total[1h])` |
| Active Users | Gauge | `active_users_total` |
| Cart Abandonment | Gauge | `1 - (cart_to_order_ratio)` |
| Payment Success Rate | Gauge | `payment_completed / payment_created` |

### Dashboard Import

```bash
# Grafana dashboard IDs (pre-configured)
# Service Health: 12345
# Infrastructure: 12346
# Business Metrics: 12347

# Import via API
curl -X POST http://admin:admin@localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d '{"dashboard": <dashboard_json>, "overwrite": true}'
```

---

## Alerting Rules

### Alertmanager Configuration

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
      repeat_interval: 1h
    - match:
        severity: warning
      receiver: 'slack-warnings'
      repeat_interval: 4h

receivers:
  - name: 'default'
    email_configs:
      - to: ops@marketplace.com
        from: prometheus@marketplace.com
        smarthost: smtp.marketplace.com:587

  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: <pagerduty-service-key>

  - name: 'slack-warnings'
    slack_configs:
      - api_url: https://hooks.slack.com/services/<webhook-url>
        channel: '#marketplace-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

### Alert Rules Summary

| Alert | Condition | Severity | Notification |
|-------|-----------|----------|-------------|
| ServiceDown | `up == 0` for 1m | Critical | PagerDuty + Email |
| HighErrorRate | Error rate > 5% for 5m | Critical | PagerDuty + Email |
| HighLatency | p99 > 1s for 5m | Warning | Slack |
| HighMemoryUsage | Memory > 400MB for 5m | Warning | Slack |
| DiskSpaceLow | Disk < 10% for 10m | Critical | PagerDuty + Email |
| KafkaConsumerLag | Lag > 10000 | Warning | Slack |
| DBConnectionPoolExhausted | Pool usage > 90% | Critical | PagerDuty |
| PaymentFailureRate | Payment failure > 10% | Critical | PagerDuty + Email |

---

## Log Aggregation

### Architecture

```
Service Logs (JSON)
       │
       ▼
┌──────────────┐     ┌──────────────┐
│  Filebeat    │────>│  Elasticsearch│
│  (log shipper)│    │  (storage)    │
└──────────────┘     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Kibana     │
                     │  (visualization)│
                     └──────────────┘
```

### Filebeat Configuration

```yaml
# filebeat.yml
filebeat.inputs:
  - type: container
    paths:
      - /var/lib/docker/containers/*/*.log
    json.message_key: message
    json.keys_under_root: true
    fields:
      log_type: container
    fields_under_root: true

processors:
  - add_docker_metadata: ~
  - drop_fields:
      fields: ["host", "input", "log"]

output.elasticsearch:
  hosts: ['http://elasticsearch:9200']
  index: "marketplace-logs-%{+yyyy.MM.dd}"
```

### Kibana Index Pattern

```
marketplace-logs-*
```

### Log Query Examples

```
# Find all error logs
level: error

# Find logs for a specific service
service.name: order-service

# Find logs for a specific request
http.request.id: "req_abc123"

# Find 5xx errors
http.response.status_code >= 500

# Find slow requests
http.request.duration_ms > 1000
```

---

## Distributed Tracing

### OpenTelemetry Setup

```python
# In each service, add OpenTelemetry instrumentation
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure tracer
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Create tracer
tracer = trace.get_tracer(__name__)
```

### Tracing Architecture

```
Client Request
     │
     │  X-Request-ID: abc123
     ▼
┌──────────────┐
│   Gateway    │  ← Span: gateway.request
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   BFF        │  ← Span: bff.aggregate
└──────┬───────┘
       │
       ├──► Auth Service  ← Span: auth.login
       ├──► Catalog       ← Span: catalog.get
       ├──► Cart          ← Span: cart.get
       └──► Order         ← Span: order.create
```

### Jaeger Configuration

```yaml
# jaeger.yml (for Docker Compose)
version: '3'
services:
  jaeger:
    image: jaegertracing/all-in-one:1.52
    ports:
      - "16686:16686"  # UI
      - "14268:14268"  # Collector HTTP
      - "6831:6831/udp" # Agent
    environment:
      - COLLECTOR_ZIPKIN_HTTP_PORT=9411
```

---

## Custom Metrics

### Service-Level Metrics

Each service exposes custom metrics:

```python
from prometheus_client import Counter, Histogram, Gauge

# Request counter
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'path', 'status']
)

# Request duration
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'path']
)

# Active connections
ACTIVE_CONNECTIONS = Gauge(
    'http_connections_active',
    'Number of active connections'
)

# Business metrics
ORDERS_CREATED = Counter(
    'orders_created_total',
    'Total orders created'
)

PAYMENT_AMOUNT = Counter(
    'payment_amount_total',
    'Total payment amount',
    ['currency']
)
```

### Metrics Endpoints

| Service | Endpoint | Port |
|---------|----------|------|
| Gateway | `/metrics` | 8080 |
| Auth Service | `/metrics` | 50052 |
| Catalog Service | `/metrics` | 8080 |
| Cart Service | `/metrics` | 8081 |
| Order Service | `/metrics` | 8085 |
| Payment Service | `/metrics` | 8082 |
| Notification Service | `/metrics` | 8086 |
| Search Service | `/metrics` | 8083 |
| Seller Service | `/metrics` | 8085 |
| Admin Service | `/metrics` | 8085 |
| BFF Service | `/metrics` | 8085 |

---

## Related Documentation

- [Main README](../README.md) — Project overview
- [Deployment Guide](deployment.md) — Production deployment
- [Development Guide](development.md) — Local monitoring setup
