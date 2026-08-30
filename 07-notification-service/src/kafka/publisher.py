"""Async Kafka publisher for outbound notification events."""

import json
import logging
from typing import Any

from confluent_kafka import Producer, KafkaException

from src.config import settings

logger = logging.getLogger(__name__)


class NotificationKafkaPublisher:
    """Publishes notification lifecycle events to Kafka."""

    def __init__(self) -> None:
        self._producer: Producer | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def setup(self) -> None:
        self._producer = Producer(
            {
                "bootstrap.servers": settings.kafka_brokers,
                "acks": "all",
                "retries": 3,
            }
        )
        logger.info("Kafka producer configured with brokers=%s", settings.kafka_brokers)

    def close(self) -> None:
        if self._producer:
            self._producer.flush()
            self._producer = None
            logger.info("Kafka producer closed")

    # ------------------------------------------------------------------
    # Publish helpers
    # ------------------------------------------------------------------
    async def _publish(self, topic: str, event: dict[str, Any]) -> None:
        if not self._producer:
            self.setup()

        payload = json.dumps(event).encode("utf-8")
        future = []

        def _delivery_report(err, msg):
            if err is not None:
                logger.error("Kafka delivery error: %s", err)
            else:
                logger.debug(
                    "Delivered to %s [%d] offset %d",
                    msg.topic(),
                    msg.partition(),
                    msg.offset(),
                )
            future.append(None)

        self._producer.produce(
            topic,
            payload,
            callback=_delivery_report,
        )
        self._producer.poll(0)  # trigger delivery report
        # brief wait for the async delivery callback
        while not future:
            await _sleep(0.01)
        self._producer.poll(0)

    async def publish_email_sent(self, event: dict[str, Any]) -> None:
        """Publish a notification event indicating an email was sent."""
        await self._publish("notification.email.sent", event)

    async def publish_sms_sent(self, event: dict[str, Any]) -> None:
        """Publish a notification event indicating an SMS was sent."""
        await self._publish("notification.sms.sent", event)

    async def publish_push_sent(self, event: dict[str, Any]) -> None:
        """Publish a notification event indicating a push notification was sent."""
        await self._publish("notification.push.sent", event)


# tiny helper to avoid importing asyncio in top-level scope
async def _sleep(seconds: float) -> None:
    import asyncio
    await asyncio.sleep(seconds)
