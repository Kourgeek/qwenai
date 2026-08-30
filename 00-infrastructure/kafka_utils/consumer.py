"""Generic async Kafka consumer with auto/manual commit, error handling,
graceful shutdown, consumer group management, and message deserialization.

Designed to be dropped into any service with minimal configuration.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Coroutine

from confluent_kafka import Consumer, KafkaError, KafkaException, Message

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class KafkaConsumerConfig:
    """Configuration for the generic Kafka consumer."""

    brokers: str = "localhost:9092"
    group_id: str = "generic-consumer-group"
    topics: list[str] = field(default_factory=list)
    auto_commit: bool = True
    auto_commit_interval_ms: int = 5000
    enable_auto_commit: bool = True
    auto_offset_reset: str = "latest"  # 'earliest' | 'latest'
    session_timeout_ms: int = 30000
    heartbeat_interval_ms: int = 3000
    max_poll_interval_ms: int = 300000
    max_poll_records: int = 500
    consumer_poll_timeout: float = 1.0
    retry_max_retries: int = 3
    retry_backoff_ms: int = 100
    max_delay_ms: int = 30000
    deserializer: Callable[[bytes], Any] | None = None
    extra_conf: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------

class KafkaConsumerError(Exception):
    """Base exception for consumer errors."""


class KafkaDeserializationError(KafkaConsumerError):
    """Raised when message deserialization fails."""


class KafkaProcessingError(KafkaConsumerError):
    """Raised when message processing fails."""


# ---------------------------------------------------------------------------
# Consumer
# ---------------------------------------------------------------------------

class AsyncKafkaConsumer:
    """Async Kafka consumer with lifecycle management.

    Usage::

        consumer = AsyncKafkaConsumer(KafkaConsumerConfig(
            brokers="kafka:9092",
            group_id="my-service",
            topics=["order.created", "payment.completed"],
        ))

        @consumer.on_message("order.created")
        async def handle_order(msg: dict):
            print(f"Got: {msg}")

        @consumer.on_message("payment.completed")
        async def handle_payment(msg: dict):
            print(f"Got: {msg}")

        await consumer.start()
        try:
            await consumer.run()  # blocks until stop() is called
        finally:
            await consumer.stop()
    """

    def __init__(
        self,
        config: KafkaConsumerConfig | None = None,
        name: str = "consumer",
    ) -> None:
        self._config = config or KafkaConsumerConfig()
        self._name = name
        self._consumer: Consumer | None = None
        self._running = False
        self._poll_task: asyncio.Task | None = None
        self._message_handlers: dict[str, list[Callable]] = {}
        self._error_handler: Callable[[Exception], Coroutine] | None = None
        self._on_commit: Callable | None = None
        self._metrics: dict[str, int] = {
            "messages_consumed": 0,
            "messages_processed": 0,
            "messages_failed": 0,
            "commits": 0,
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def setup(self) -> None:
        """Create and configure the underlying confluent-kafka Consumer."""
        if self._consumer:
            return

        conf = {
            "bootstrap.servers": self._config.brokers,
            "group.id": self._config.group_id,
            "enable.auto.commit": self._config.enable_auto_commit,
            "auto.commit.interval.ms": self._config.auto_commit_interval_ms,
            "auto.offset.reset": self._config.auto_offset_reset,
            "session.timeout.ms": self._config.session_timeout_ms,
            "heartbeat.interval.ms": self._config.heartbeat_interval_ms,
            "max.poll.interval.ms": self._config.max_poll_interval_ms,
            "max.poll.records": self._config.max_poll_records,
            **self._config.extra_conf,
        }
        self._consumer = Consumer(conf)
        self._consumer.subscribe(
            self._config.topics,
            on_assign=self._on_partitions_assigned,
            on_revoke=self._on_partitions_revoked,
        )
        logger.info(
            "[%s] Consumer configured: group=%s topics=%s",
            self._name, self._config.group_id, self._config.topics,
        )

    async def start(self) -> None:
        """Start the consumer and its polling loop."""
        if self._running:
            return

        self.setup()
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info("[%s] Consumer started, group=%s", self._name, self._config.group_id)

    async def stop(self, timeout: float = 10.0) -> None:
        """Gracefully stop the consumer and close the session."""
        if not self._running:
            return
        self._running = False

        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None

        if self._consumer:
            self._consumer.close()
            self._consumer = None
            logger.info("[%s] Consumer stopped", self._name)

    @property
    def is_running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------
    # Message handling
    # ------------------------------------------------------------------

    def on_message(self, topic: str) -> Callable:
        """Decorator to register a message handler for a topic.

        The handler receives the deserialized message dict.
        """
        def decorator(func: Callable[[dict], Coroutine]) -> Callable[[dict], Coroutine]:
            self._message_handlers.setdefault(topic, []).append(func)
            logger.info("[%s] Registered handler for topic=%s", self._name, topic)
            return func
        return decorator

    def on_error(self, func: Callable[[Exception], Coroutine]) -> Callable:
        """Decorator to register a global error handler."""
        self._error_handler = func
        return func

    async def _dispatch_message(self, topic: str, message_dict: dict) -> None:
        """Dispatch a deserialized message to registered handlers."""
        handlers = self._message_handlers.get(topic, [])
        if not handlers:
            logger.warning("[%s] No handler registered for topic=%s", self._name, topic)
            return

        for handler in handlers:
            try:
                await handler(message_dict)
                self._metrics["messages_processed"] += 1
            except Exception as exc:
                self._metrics["messages_failed"] += 1
                logger.error(
                    "[%s] Handler error for topic=%s: %s",
                    self._name, topic, exc,
                )
                if self._error_handler:
                    try:
                        await self._error_handler(exc)
                    except Exception:
                        logger.exception("Error handler itself failed")

    # ------------------------------------------------------------------
    # Polling loop
    # ------------------------------------------------------------------

    async def _poll_loop(self) -> None:
        """Main polling loop — runs until stop() is called."""
        while self._running:
            try:
                msg = self._consumer.poll(timeout=self._config.consumer_poll_timeout)
            except KafkaException as exc:
                logger.error("[%s] Poll error: %s", self._name, exc)
                if self._error_handler:
                    try:
                        await self._error_handler(exc)
                    except Exception:
                        pass
                await asyncio.sleep(1.0)
                continue

            if msg is None:
                continue

            # End of partition
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.debug("[%s] End of partition reached", self._name)
                else:
                    logger.error("[%s] Kafka error: %s", self._name, msg.error())
                continue

            # Update metrics
            self._metrics["messages_consumed"] += 1

            # Deserialize
            try:
                raw_value = msg.value()
                if raw_value is None:
                    logger.warning("[%s] Null message value on topic=%s", self._name, msg.topic())
                    continue
                if isinstance(raw_value, bytes):
                    if self._config.deserializer:
                        message_dict = self._config.deserializer(raw_value)
                    else:
                        message_dict = self._deserialize_json(raw_value)
                else:
                    message_dict = raw_value
            except KafkaDeserializationError:
                raise
            except Exception as exc:
                self._metrics["messages_failed"] += 1
                logger.error(
                    "[%s] Deserialization error on topic=%s: %s",
                    self._name, msg.topic(), exc,
                )
                # Commit to skip bad message
                if not self._config.enable_auto_commit:
                    try:
                        self._consumer.commit(asynchronous=True)
                    except Exception:
                        pass
                continue

            # Dispatch
            topic = msg.topic()
            await self._dispatch_message(topic, message_dict)

            # Manual commit
            if not self._config.enable_auto_commit:
                try:
                    msg.commit()
                    self._metrics["commits"] += 1
                except KafkaException as exc:
                    logger.error("[%s] Commit error: %s", self._name, exc)

    def _deserialize_json(self, raw: bytes) -> dict:
        """Deserialize JSON bytes to dict."""
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise KafkaDeserializationError(f"Failed to deserialize message: {exc}") from exc

    # ------------------------------------------------------------------
    # Partition rebalance callbacks
    # ------------------------------------------------------------------

    def _on_partitions_assigned(self, consumer: Consumer, topics: list) -> None:
        logger.info("[%s] Partitions assigned: %s", self._name, topics)

    def _on_partitions_revoked(self, consumer: Consumer, topics: list) -> None:
        logger.info("[%s] Partitions revoked: %s", self._name, topics)

    # ------------------------------------------------------------------
    # Run / block
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """Run the consumer until stopped. Blocks the calling coroutine."""
        if not self._running:
            await self.start()
        # _poll_loop is already running as a task
        try:
            while self._running:
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            pass

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def get_metrics(self) -> dict[str, int]:
        """Return consumer metrics snapshot."""
        return dict(self._metrics)

    def reset_metrics(self) -> None:
        """Reset all consumer metrics to zero."""
        self._metrics = {k: 0 for k in self._metrics}

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def consumer_group(self) -> str:
        return self._config.group_id

    @property
    def subscribed_topics(self) -> list[str]:
        return list(self._config.topics)
