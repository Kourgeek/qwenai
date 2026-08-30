"""Async Kafka publisher for Order-domain events."""

from __future__ import annotations

import json
import logging
from typing import Any

from confluent_kafka import Producer

from src.config import settings

logger = logging.getLogger(__name__)


class OrderKafkaPublisher:
    """Wrapper around ``confluent_kafka.Producer`` with helper methods."""

    def __init__(self, broker: str | None = None) -> None:
        conf: dict[str, Any] = {"bootstrap.servers": broker or settings.kafka_brokers}
        self.producer = Producer(conf)

    def _deliver(self, topic: str, key: str, payload: dict[str, Any]) -> None:
        """Serialise *payload* and deliver to *topic* with *key*."""
        self.producer.produce(
            topic=topic,
            key=key.encode("utf-8"),
            value=json.dumps(payload).encode("utf-8"),
            on_delivery=self._delivery_report,
        )
        self.producer.poll(0)

    @staticmethod
    def _delivery_report(err: Any, msg: Any) -> None:
        if err is not None:
            logger.error("Kafka delivery error: %s", err)
        else:
            logger.debug(
                "Delivered to %s [%d] at offset %d",
                msg.topic(),
                msg.partition(),
                msg.offset(),
            )

    async def publish_order_created(
        self, order_id: int, user_id: int, total_amount: float
    ) -> None:
        """Emit an ``order.created`` domain event."""
        payload = {
            "event": "order.created",
            "order_id": order_id,
            "user_id": user_id,
            "total_amount": total_amount,
        }
        self._deliver(settings.kafka_order_created_topic, str(order_id), payload)
        logger.info("Published order.created for order_id=%s", order_id)

    async def publish_order_status_changed(
        self, order_id: int, old_status: str, new_status: str
    ) -> None:
        """Emit an ``order.status_changed`` domain event."""
        payload = {
            "event": "order.status_changed",
            "order_id": order_id,
            "old_status": old_status,
            "new_status": new_status,
        }
        self._deliver(
            settings.kafka_order_status_changed_topic, str(order_id), payload
        )
        logger.info(
            "Published order.status_changed for order_id=%s (%s -> %s)",
            order_id,
            old_status,
            new_status,
        )

    async def close(self) -> None:
        """Flush and close the underlying producer."""
        self.producer.flush(timeout=10)
