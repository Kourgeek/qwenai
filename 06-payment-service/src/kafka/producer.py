"""
Async Kafka producer for payment domain events.

Publishes payment lifecycle events to the ``marketplace-events``
Kafka topic using the ``confluent-kafka`` library.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from confluent_kafka import Producer

from src.config import settings

logger = logging.getLogger(__name__)


class PaymentKafkaProducer:
    """Wraps confluent_kafka.Producer with payment-domain helpers."""

    def __init__(self, brokers: str | None = None, topic: str | None = None) -> None:
        self._topic = topic or settings.kafka_topic
        conf = {
            "bootstrap.servers": brokers or settings.kafka_brokers,
            "client.id": "payment-service",
            "acks": "all",
            "retries": 3,
        }
        self._producer = Producer(conf)
        self._dr_listeners_installed = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _ensure_dr(self) -> None:
        """Register delivery-report callbacks (idempotent)."""
        if self._dr_listeners_installed:
            return
        self._dr_listeners_installed = True

    def _delivery_report(self, err, msg) -> None:
        if err:
            logger.error("Kafka delivery error: %s", err)
        else:
            logger.debug(
                "Kafka message delivered: topic=%s partition=%d offset=%d",
                msg.topic(),
                msg.partition(),
                msg.offset(),
            )

    async def publish(self, event: dict[str, Any]) -> None:
        """
        Publish a single event dict to the Kafka topic.

        Serialises the dict as JSON and fires-and-forgets.
        """
        self._ensure_dr()
        payload = json.dumps(event).encode("utf-8")
        self._producer.produce(
            self._topic,
            key=event.get("payment_id", "").encode("utf-8"),
            value=payload,
            callback=self._delivery_report,
        )
        # Flush so that in-process errors surface during tests
        self._producer.poll(0)
        self._producer.flush(1.0)
        logger.info("Kafka event published: %s", event.get("event_type"))

    # ------------------------------------------------------------------
    # Domain helpers
    # ------------------------------------------------------------------

    async def publish_payment_completed(
        self,
        payment_id: str,
        order_id: str,
        amount: float,
        currency: str = "RUB",
        provider: str = "STRIPE",
    ) -> None:
        await self.publish(
            {
                "event_type": "payment.completed",
                "payment_id": payment_id,
                "order_id": order_id,
                "amount": float(amount),
                "currency": currency,
                "provider": provider,
                "timestamp": self._now_iso(),
            }
        )

    async def publish_payment_failed(
        self,
        payment_id: str,
        order_id: str,
        error: str,
    ) -> None:
        await self.publish(
            {
                "event_type": "payment.failed",
                "payment_id": payment_id,
                "order_id": order_id,
                "error": error,
                "timestamp": self._now_iso(),
            }
        )

    async def publish_refund_completed(
        self,
        payment_id: str,
        order_id: str,
        refund_id: str,
        amount: float,
        currency: str = "RUB",
    ) -> None:
        await self.publish(
            {
                "event_type": "refund.completed",
                "payment_id": payment_id,
                "order_id": order_id,
                "refund_id": refund_id,
                "amount": float(amount),
                "currency": currency,
                "timestamp": self._now_iso(),
            }
        )

    @staticmethod
    def _now_iso() -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()

    def close(self) -> None:
        self._producer.flush(2.0)


payment_kafka_producer = PaymentKafkaProducer()
