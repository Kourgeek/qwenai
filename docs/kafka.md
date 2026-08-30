# Kafka Events Documentation

Comprehensive documentation of Kafka topics, message schemas, producer/consumer patterns, and event sourcing architecture in the HyperScale Marketplace.

---

## Table of Contents

- [Overview](#overview)
- [Infrastructure](#infrastructure)
- [Topics](#topics)
- [Message Schemas](#message-schemas)
- [Producer Patterns](#producer-patterns)
- [Consumer Patterns](#consumer-patterns)
- [Event Sourcing](#event-sourcing)
- [Data Flow](#data-flow)
- [Best Practices](#best-practices)

---

## Overview

Kafka is used for asynchronous inter-service communication, enabling event-driven architecture patterns across the marketplace. Services publish events to topics and subscribe to events from other services.

### Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Order      │    │  Payment    │    │  Catalog    │
│  Service    │    │  Service    │    │  Service    │
│  (Producer) │    │  (Producer) │    │  (Consumer) │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       ▼                  ▼                  │
┌─────────────────────────────────────────────────────┐
│                    Kafka Cluster                     │
│                                                      │
│  ┌──────────────────┐  ┌──────────────────┐        │
│  │ order.created    │  │ payment.completed│        │
│  │ order.status_    │  │ payment.failed   │        │
│  │   changed        │  │ marketplace-     │        │
│  │                  │  │ events           │        │
│  └──────────────────┘  └──────────────────┘        │
└────────────────────────┬────────────────────────────┘
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Notification│  │  Search     │  │  Analytics  │
│  Service    │  │  Service    │  │  (future)   │
│ (Consumer)  │  │  (Consumer) │  │  (Consumer) │
└─────────────┘  └─────────────┘  └─────────────┘
```

---

## Infrastructure

### Kafka Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| **Broker** | `kafka:9092` (internal) / `localhost:9092` (host) | Kafka broker address |
| **Zookeeper** | `zookeeper:2181` | Zookeeper for Kafka coordination |
| **Replication Factor** | 1 | Single-node deployment |
| **Min In-Sync Replicas** | 1 | Minimum replicas for ack |
| **Auto Create Topics** | `true` | Auto-create topics on first publish |
| **Transaction Log ISR** | 1 | Min ISR for transaction logs |
| **Transaction Log Replication** | 1 | Replication factor for transaction logs |

### Docker Compose

```yaml
zookeeper:
  image: confluentinc/cp-zookeeper:7.5.0
  environment:
    ZOOKEEPER_CLIENT_PORT: 2181
    ZOOKEEPER_TICK_TIME: 2000

kafka:
  image: confluentinc/cp-kafka:7.5.0
  environment:
    KAFKA_BROKER_ID: 1
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
    KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT
    KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
    KAFKA_MIN_INSYNC_REPLICAS: 1
  depends_on:
    - zookeeper
```

---

## Topics

### Topic Summary

| Topic | Partitions | Retention | Producer | Consumers |
|-------|-----------|-----------|----------|-----------|
| `order.created` | 3 | 7 days | order-service | notification-service |
| `order.status_changed` | 3 | 7 days | order-service | notification-service |
| `payment.completed` | 3 | 30 days | payment-service | notification-service |
| `payment.failed` | 3 | 30 days | payment-service | notification-service |
| `marketplace-events` | 6 | 14 days | All services | Analytics, Search |

### Topic Details

#### `order.created`

| Property | Value |
|----------|-------|
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Key** | `user_id` |
| **Schema** | `OrderCreatedEvent` |

#### `order.status_changed`

| Property | Value |
|----------|-------|
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Key** | `order_id` |
| **Schema** | `OrderStatusChangedEvent` |

#### `payment.completed`

| Property | Value |
|----------|-------|
| **Partitions** | 3 |
| **Retention** | 30 days |
| **Key** | `payment_id` |
| **Schema** | `PaymentCompletedEvent` |

#### `payment.failed`

| Property | Value |
|----------|-------|
| **Partitions** | 3 |
| **Retention** | 30 days |
| **Key** | `payment_id` |
| **Schema** | `PaymentFailedEvent` |

#### `marketplace-events`

| Property | Value |
|----------|-------|
| **Partitions** | 6 |
| **Retention** | 14 days |
| **Key** | `event_type` |
| **Schema** | `GenericMarketplaceEvent` |

---

## Message Schemas

### OrderCreatedEvent

```json
{
  "event_type": "order.created",
  "event_id": "evt_abc123",
  "event_time": "2026-08-03T10:00:00Z",
  "order_id": "ord_def456",
  "user_id": "usr_abc123",
  "cart_id": "cart_xyz789",
  "total_amount": 249.97,
  "currency": "USD",
  "item_count": 2,
  "items": [
    {
      "product_id": "prod_abc123",
      "product_name": "Wireless Headphones",
      "sku": "WH-001",
      "quantity": 1,
      "unit_price": 99.99,
      "total_price": 99.99
    },
    {
      "product_id": "prod_def456",
      "product_name": "Phone Case",
      "sku": "PC-001",
      "quantity": 2,
      "unit_price": 74.99,
      "total_price": 149.98
    }
  ],
  "shipping_address": {
    "full_name": "John Doe",
    "line1": "123 Main St",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "US"
  },
  "payment_method": "stripe_card"
}
```

### OrderStatusChangedEvent

```json
{
  "event_type": "order.status_changed",
  "event_id": "evt_def789",
  "event_time": "2026-08-03T10:05:00Z",
  "order_id": "ord_def456",
  "user_id": "usr_abc123",
  "old_status": "pending",
  "new_status": "processing",
  "changed_by": "system",
  "tracking_number": null
}
```

### PaymentCompletedEvent

```json
{
  "event_type": "payment.completed",
  "event_id": "evt_ghi012",
  "event_time": "2026-08-03T10:10:00Z",
  "payment_id": "pay_ghi789",
  "order_id": "ord_def456",
  "user_id": "usr_abc123",
  "amount": 24997,
  "currency": "USD",
  "provider": "stripe",
  "provider_payment_id": "pi_1234567890",
  "payment_method": "pm_card_visa"
}
```

### PaymentFailedEvent

```json
{
  "event_type": "payment.failed",
  "event_id": "evt_jkl345",
  "event_time": "2026-08-03T10:12:00Z",
  "payment_id": "pay_ghi789",
  "order_id": "ord_def456",
  "user_id": "usr_abc123",
  "amount": 24997,
  "currency": "USD",
  "provider": "stripe",
  "provider_error": "card_declined",
  "provider_error_code": "card_declined"
}
```

### GenericMarketplaceEvent

```json
{
  "event_type": "product.created",
  "event_id": "evt_mno678",
  "event_time": "2026-08-03T11:00:00Z",
  "source_service": "catalog-service",
  "entity_type": "product",
  "entity_id": "prod_abc123",
  "data": {
    "name": "Wireless Headphones",
    "price": 99.99,
    "category_id": "cat_123",
    "is_active": true
  }
}
```

---

## Producer Patterns

### Order Service Producer

```python
# 05-order-service/src/kafka/publisher.py
from kafka import KafkaProducer
import json
import uuid
from datetime import datetime

class OrderKafkaPublisher:
    def __init__(self, broker: str):
        self.producer = KafkaProducer(
            bootstrap_servers=broker,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3
        )

    async def publish_order_created(self, order_data: dict):
        """Publish order.created event."""
        event = {
            "event_type": "order.created",
            "event_id": str(uuid.uuid4()),
            "event_time": datetime.utcnow().isoformat(),
            **order_data
        }
        future = self.producer.send(
            'order.created',
            key=order_data['user_id'],
            value=event
        )
        future.add_errback(self._on_error)
        return future

    async def publish_order_status_changed(self, order_id: str, old_status: str, new_status: str):
        """Publish order.status_changed event."""
        event = {
            "event_type": "order.status_changed",
            "event_id": str(uuid.uuid4()),
            "event_time": datetime.utcnow().isoformat(),
            "order_id": order_id,
            "old_status": old_status,
            "new_status": new_status
        }
        self.producer.send(
            'order.status_changed',
            key=order_id,
            value=event
        )

    def _on_error(self, exc):
        print(f"Kafka publish error: {exc}")

    async def close(self):
        await self.producer.flush()
        self.producer.close()
```

### Payment Service Producer

```python
# 06-payment-service/src/kafka/producer.py
from kafka import KafkaProducer
import json
import uuid
from datetime import datetime

class PaymentKafkaProducer:
    def __init__(self, broker: str):
        self.producer = KafkaProducer(
            bootstrap_servers=broker,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3
        )

    async def publish_payment_completed(self, payment_data: dict):
        """Publish payment.completed event."""
        event = {
            "event_type": "payment.completed",
            "event_id": str(uuid.uuid4()),
            "event_time": datetime.utcnow().isoformat(),
            **payment_data
        }
        self.producer.send(
            'payment.completed',
            key=payment_data['payment_id'],
            value=event
        )

    async def publish_payment_failed(self, payment_data: dict):
        """Publish payment.failed event."""
        event = {
            "event_type": "payment.failed",
            "event_id": str(uuid.uuid4()),
            "event_time": datetime.utcnow().isoformat(),
            **payment_data
        }
        self.producer.send(
            'payment.failed',
            key=payment_data['payment_id'],
            value=event
        )

    async def close(self):
        await self.producer.flush()
        self.producer.close()
```

---

## Consumer Patterns

### Notification Service Consumer

```python
# 07-notification-service/src/kafka/consumer.py
from kafka import KafkaConsumer
import json

class NotificationConsumer:
    def __init__(self, broker: str, group_id: str):
        self.consumer = KafkaConsumer(
            bootstrap_servers=broker,
            group_id=group_id,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        self.consumer.subscribe([
            'order.created',
            'order.status_changed',
            'payment.completed',
            'payment.failed'
        ])

    def start(self):
        """Start consuming events."""
        for message in self.consumer:
            event = message.value
            self._handle_event(event)

    def _handle_event(self, event: dict):
        """Route events to appropriate handlers."""
        event_type = event.get('event_type')

        if event_type == 'order.created':
            self._send_order_confirmation(event)
        elif event_type == 'order.status_changed':
            self._send_status_update(event)
        elif event_type == 'payment.completed':
            self._send_payment_confirmation(event)
        elif event_type == 'payment.failed':
            self._send_payment_failure(event)

    def _send_order_confirmation(self, event: dict):
        """Send order confirmation email."""
        # Send email notification
        pass

    def _send_status_update(self, event: dict):
        """Send order status update notification."""
        # Send push/email notification
        pass

    def _send_payment_confirmation(self, event: dict):
        """Send payment confirmation."""
        # Send payment receipt
        pass

    def _send_payment_failure(self, event: dict):
        """Send payment failure notification."""
        # Send payment failure alert
        pass
```

### Search Service Consumer

```python
# 08-search-service/src/kafka/consumer.py
from kafka import KafkaConsumer
import json

class SearchConsumer:
    def __init__(self, broker: str):
        self.consumer = KafkaConsumer(
            bootstrap_servers=broker,
            group_id='search-service-group',
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        self.consumer.subscribe(['marketplace-events'])

    def start(self):
        """Start consuming marketplace events."""
        for message in self.consumer:
            event = message.value
            self._index_event(event)

    def _index_event(self, event: dict):
        """Index product events into Elasticsearch."""
        event_type = event.get('event_type')

        if event_type in ('product.created', 'product.updated'):
            self._index_product(event)
        elif event_type == 'product.deleted':
            self._delete_product(event)

    def _index_product(self, event: dict):
        """Index product into Elasticsearch."""
        pass

    def _delete_product(self, event: dict):
        """Remove product from Elasticsearch."""
        pass
```

---

## Event Sourcing

### Architecture

```
                    ┌─────────────────┐
                    │   Event Store    │
                    │   (Kafka Topics) │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │  Order       │ │  Payment     │ │  Catalog     │
     │  Projection  │ │  Projection  │ │  Projection  │
     └──────────────┘ └──────────────┘ └──────────────┘
```

### Event Sourcing Pattern

```
Command → Aggregate → Apply Event → Persist Event → Publish Event
                                    │
                                    ▼
                              Update Projections
                                    │
                                    ▼
                              Query Ready
```

### Key Events for Event Sourcing

| Aggregate | Events |
|-----------|--------|
| **Order** | `order.created`, `order.status_changed`, `order.cancelled` |
| **Payment** | `payment.created`, `payment.completed`, `payment.failed`, `payment.refunded` |
| **Product** | `product.created`, `product.updated`, `product.deleted`, `product.price_changed` |
| **Cart** | `cart.item_added`, `cart.item_updated`, `cart.item_removed`, `cart.cleared` |

---

## Data Flow

### Order Creation Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Order   │────>│  Kafka   │────>│  Notify  │
│  Service │     │  (topic) │     │  Service │
└──────────┘     └──────────┘     └──────────┘
     │                                     │
     │  (synchronous)                      │  (async)
     ▼                                     ▼
┌──────────┐                       ┌──────────┐
│  Cart    │                       │  Email   │
│  Service │                       │  / Push  │
└──────────┘                       └──────────┘
     │
     ▼
┌──────────┐
│ Catalog  │
│ Service  │
└──────────┘
```

### Payment Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Payment │────>│  Kafka   │────>│  Notify  │
│  Service │     │  (topic) │     │  Service │
└──────────┘     └──────────┘     └──────────┘
     │                                     │
     │  (webhook)                          │  (async)
     ▼                                     ▼
┌──────────┐                       ┌──────────┐
│  Stripe  │                       │  Email   │
│  / Yoo   │<──────────────────────│  / Push  │
│  Money   │   Webhook Response    │  / SMS   │
└──────────┘                       └──────────┘
```

---

## Best Practices

### Topic Naming

| Rule | Example |
|------|---------|
| Use dot notation for namespaces | `order.created` |
| Use past tense for events | `order.created` (not `create_order`) |
| Use consistent naming across services | `payment.completed`, not `payment_done` |

### Event Design

| Rule | Description |
|------|-------------|
| Include event_id | Unique identifier for deduplication |
| Include event_time | Timestamp for ordering |
| Include source_service | Service that published the event |
| Make events immutable | Never modify published events |
| Use backward-compatible schemas | Add fields, never remove |

### Consumer Design

| Rule | Description |
|------|-------------|
| Idempotent processing | Handle duplicate events gracefully |
| Handle failures | Retry logic with exponential backoff |
| Commit offsets carefully | Commit after successful processing |
| Monitor lag | Alert on consumer lag thresholds |

### Production Considerations

| Setting | Recommendation |
|---------|---------------|
| Replication Factor | 3 (production) |
| Min ISR | 2 (production) |
| Retention | 30+ days for financial events |
| Partitions | Scale based on throughput |
| Schema Registry | Use for schema evolution |
| Security | Enable TLS and SASL |

---

## Related Documentation

- [Services Overview](services.md) — Service architecture
- [Order Service API](api/order-service.md) — Order events
- [Payment Service API](api/payment-service.md) — Payment events
- [Deployment Guide](deployment.md) — Production Kafka setup
