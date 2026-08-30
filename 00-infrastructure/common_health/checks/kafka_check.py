"""Kafka health check using confluent_kafka."""

from __future__ import annotations

import logging
from typing import Any

from ..health_check import HealthCheck, HealthCheckResult

logger = logging.getLogger(__name__)


class KafkaHealthCheck(HealthCheck):
    """Check Kafka broker connectivity via ``librdkafka`` metadata request."""

    def __init__(self, brokers: str, timeout: float = 5.0) -> None:
        super().__init__(name="kafka")
        self._brokers = brokers
        self._timeout = timeout

    async def check(self) -> HealthCheckResult:
        from confluent_kafka import Consumer, KafkaException, KafkaError

        conf = {
            "bootstrap.servers": self._brokers,
            "client.id": f"{self.name}-health-check",
            "group.id": f"{self.name}-health-check-group",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "session.timeout.ms": 6000,
        }
        consumer = None
        try:
            consumer = Consumer(conf)
            metadata = consumer.list_metadata(timeout=self._timeout)
            brokers_info = []
            if metadata and metadata.brokers:
                for broker in metadata.brokers.values():
                    brokers_info.append({"id": broker.id, "host": broker.host, "port": broker.port})
            return HealthCheckResult(
                name=self.name,
                status="healthy",
                detail={"brokers": brokers_info, "topics": [t.name for t in (metadata.topics or [])]},
            )
        except KafkaError as exc:
            logger.warning("Kafka health check failed: %s", exc)
            return HealthCheckResult(name=self.name, status="unhealthy", error=str(exc))
        except Exception as exc:
            logger.warning("Kafka health check error: %s", exc)
            return HealthCheckResult(name=self.name, status="unhealthy", error=str(exc))
        finally:
            if consumer is not None:
                consumer.close()
