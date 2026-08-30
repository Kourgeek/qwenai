"""Async Kafka consumer for incoming marketplace events."""

import logging
from typing import Callable, Awaitable

from confluent_kafka import Consumer, KafkaError, KafkaException

from src.config import settings

logger = logging.getLogger(__name__)


class OrderKafkaConsumer:
    """Consumes order, payment, and refund events from Kafka."""

    def __init__(self) -> None:
        self._consumer: Consumer | None = None
        self._running = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def setup(self) -> None:
        """Configure and subscribe the underlying confluent-kafka Consumer."""
        self._consumer = Consumer(
            {
                "bootstrap.servers": settings.kafka_brokers,
                "group.id": "notification-service",
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
                "session.timeout.ms": "6000",
            }
        )
        topics = [
            settings.kafka_order_topic,
            settings.kafka_payment_topic,
            settings.kafka_refund_topic,
        ]
        self._consumer.subscribe(topics)
        logger.info("Kafka consumer subscribed to %s", topics)

    def start(self, loop) -> None:
        """Start the polling loop in the given event-loop thread."""
        if not self._consumer:
            self.setup()
        self._running = True
        loop.create_task(self._poll_loop())

    async def stop(self) -> None:
        """Signal the polling loop to stop and close the consumer."""
        self._running = False
        if self._consumer:
            self._consumer.close()
            self._consumer = None
        logger.info("Kafka consumer stopped")

    # ------------------------------------------------------------------
    # Internal polling
    # ------------------------------------------------------------------
    async def _poll_loop(self) -> None:
        """Continuously poll Kafka and dispatch callbacks."""
        while self._running:
            msg = self._consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.debug("End of partition reached")
                else:
                    logger.error("Kafka error: %s", msg.error())
                continue

            topic = msg.topic()
            payload = msg.value()
            try:
                payload_str = payload.decode("utf-8") if isinstance(payload, bytes) else str(payload)
            except Exception:
                payload_str = str(payload)

            logger.info("Received message on topic=%s", topic)

            # Dispatch to the appropriate callback
            if topic == settings.kafka_order_topic:
                await self._dispatch("order_created", payload_str)
            elif topic == settings.kafka_payment_topic:
                await self._dispatch("payment_completed", payload_str)
            elif topic == settings.kafka_refund_topic:
                await self._dispatch("refund_completed", payload_str)
            else:
                logger.warning("Unhandled topic: %s", topic)

    # ------------------------------------------------------------------
    # Callback registration
    # ------------------------------------------------------------------
    async def consume_order_created(self, callback: Callable[[str], Awaitable[None]]) -> None:
        """Register *callback* to be called when an order.created event arrives.

        The callback receives the raw JSON payload string.
        """
        await self._register_callback(settings.kafka_order_topic, callback)

    async def consume_payment_completed(self, callback: Callable[[str], Awaitable[None]]) -> None:
        """Register *callback* for payment.completed events."""
        await self._register_callback(settings.kafka_payment_topic, callback)

    async def consume_refund_completed(self, callback: Callable[[str], Awaitable[None]]) -> None:
        """Register *callback* for payment.refunded events."""
        await self._register_callback(settings.kafka_refund_topic, callback)

    # -- helpers --------------------------------------------------------
    _callbacks: dict[str, Callable[[str], Awaitable[None]]] = {}

    async def _register_callback(
        self, topic: str, callback: Callable[[str], Awaitable[None]]
    ) -> None:
        self._callbacks[topic] = callback
        logger.info("Registered callback for topic=%s", topic)

    async def _dispatch(self, topic: str, payload: str) -> None:
        cb = self._callbacks.get(topic)
        if cb is None:
            logger.warning("No callback registered for topic=%s", topic)
            return
        try:
            await cb(payload)
        except Exception:
            logger.exception("Callback raised for topic=%s", topic)
