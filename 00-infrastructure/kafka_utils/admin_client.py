"""Kafka Admin client utilities for topic and consumer group management.

Provides synchronous helpers for:
- Creating topics with configurable partitions/replicas
- Checking topic existence
- Listing topics
- Managing consumer groups
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from confluent_kafka import AdminClient, KafkaException, KafkaError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class TopicConfig:
    """Configuration for topic creation."""

    name: str
    num_partitions: int = 3
    replication_factor: int = 1
    config: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dict format expected by AdminClient.create_topics()."""
        return {
            "topic": self.name,
            "num_partitions": self.num_partitions,
            "replication_factor": self.replication_factor,
            "config": self.config,
        }


@dataclass
class KafkaAdminConfig:
    """Configuration for the Kafka admin client."""

    brokers: str = "localhost:9092"
    extra_conf: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Admin client wrapper
# ---------------------------------------------------------------------------

class KafkaAdminClient:
    """Wraps confluent_kafka.AdminClient with high-level topic/group operations.

    Usage::

        admin = KafkaAdminClient(KafkaAdminConfig(brokers="kafka:9092"))
        await admin.create_topics([
            TopicConfig("order.created", num_partitions=3),
            TopicConfig("payment.completed", num_partitions=3),
        ])
        if await admin.topic_exists("order.created"):
            print("Topic exists")
    """

    def __init__(self, config: KafkaAdminConfig | None = None) -> None:
        self._config = config or KafkaAdminConfig()
        self._admin = AdminClient(self._config.extra_conf | {"bootstrap.servers": self._config.brokers})

    # ------------------------------------------------------------------
    # Topic operations
    # ------------------------------------------------------------------

    async def create_topic(self, config: TopicConfig) -> bool:
        """Create a single topic. Returns True if created, False if already exists."""
        try:
            future = self._admin.create_topics([config.to_dict()])
            future.result(timeout=30)
            logger.info("Topic '%s' created with %d partitions", config.name, config.num_partitions)
            return True
        except KafkaException as exc:
            if exc.args[0].code() == KafkaError.TOPIC_ALREADY_EXISTS:
                logger.info("Topic '%s' already exists", config.name)
                return False
            logger.error("Failed to create topic '%s': %s", config.name, exc)
            raise

    async def create_topics(self, configs: list[TopicConfig]) -> list[bool]:
        """Create multiple topics. Returns list of success booleans."""
        results = []
        for config in configs:
            try:
                result = await self.create_topic(config)
                results.append(result)
            except KafkaException as exc:
                logger.error("Error creating topic '%s': %s", config.name, exc)
                results.append(False)
        return results

    async def topic_exists(self, topic_name: str) -> bool:
        """Check if a topic exists by listing topics."""
        try:
            metadata = self._admin.list_topics(timeout=10)
            return topic_name in metadata.topics
        except KafkaException as exc:
            logger.error("Error checking topic existence: %s", exc)
            return False

    async def list_topics(self) -> list[str]:
        """List all available topics."""
        try:
            metadata = self._admin.list_topics(timeout=10)
            return list(metadata.topics.keys())
        except KafkaException as exc:
            logger.error("Error listing topics: %s", exc)
            return []

    async def delete_topic(self, topic_name: str) -> bool:
        """Delete a topic. Returns True if deleted, False if not found."""
        try:
            from confluent_kafka.admin import NewTopic, DeleteTopicsResult
            # AdminClient.delete_topics is synchronous
            future = self._admin.delete_topics([topic_name])
            # Wait for completion
            for topic, fut in future.items():
                fut.result(timeout=30)
            logger.info("Topic '%s' deleted", topic_name)
            return True
        except KafkaException as exc:
            if exc.args[0].code() == KafkaError.UNKNOWN_TOPIC_OR_PARTITION:
                logger.warning("Topic '%s' does not exist", topic_name)
                return False
            logger.error("Failed to delete topic '%s': %s", topic_name, exc)
            raise

    # ------------------------------------------------------------------
    # Consumer group operations
    # ------------------------------------------------------------------

    async def list_consumer_groups(self) -> list[dict]:
        """List all consumer groups with their states."""
        groups = []
        try:
            # Use describe_groups to get all groups
            from confluent_kafka.admin import ConsumerGroupState
            # AdminClient.describe_consumer_groups returns a future
            future = self._admin.describe_consumer_groups([])
            # This will describe all groups when list is empty
            for group_name, group_desc in future.result(timeout=30).items():
                state = group_desc.state if hasattr(group_desc, 'state') else 'Unknown'
                members = len(group_desc.members) if hasattr(group_desc, 'members') else 0
                topics = [t.topic for t in group_desc.topics] if hasattr(group_desc, 'topics') else []
                groups.append({
                    "group_id": group_name,
                    "state": state,
                    "members": members,
                    "topics": topics,
                })
        except KafkaException as exc:
            logger.error("Error listing consumer groups: %s", exc)
        return groups

    async def describe_consumer_group(self, group_id: str) -> dict | None:
        """Describe a specific consumer group."""
        try:
            future = self._admin.describe_consumer_groups([group_id])
            result = future.result(timeout=30)
            group = result.get(group_id)
            if group:
                state = group.state if hasattr(group, 'state') else 'Unknown'
                members = len(group.members) if hasattr(group, 'members') else 0
                topics = [t.topic for t in group.topics] if hasattr(group, 'topics') else []
                return {
                    "group_id": group_id,
                    "state": state,
                    "members": members,
                    "topics": topics,
                }
            return None
        except KafkaException as exc:
            logger.error("Error describing consumer group '%s': %s", group_id, exc)
            return None

    async def delete_consumer_group(self, group_id: str) -> bool:
        """Delete (describe and reset) a consumer group. Note: actual deletion
        requires the group to be in Empty state."""
        try:
            # We can't directly delete groups with confluent_kafka AdminClient
            # This is a placeholder for the operation
            logger.warning(
                "Consumer group '%s' cannot be deleted programmatically with confluent_kafka. "
                "Use kafka-consumer-groups.sh --bootstrap-server %s --group %s --delete",
                group_id, self._config.brokers, group_id,
            )
            return False
        except KafkaException as exc:
            logger.error("Error deleting consumer group '%s': %s", group_id, exc)
            return False

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    async def ensure_topics(self, configs: list[TopicConfig]) -> list[bool]:
        """Ensure topics exist, creating them if they don't.

        Returns list of booleans indicating whether each topic was created.
        """
        results = []
        for config in configs:
            exists = await self.topic_exists(config.name)
            if exists:
                results.append(False)
            else:
                created = await self.create_topic(config)
                results.append(created)
        return results

    def get_admin_client(self) -> AdminClient:
        """Return the raw AdminClient instance for advanced operations."""
        return self._admin

    def close(self) -> None:
        """Close the admin client."""
        self._admin = None
        logger.info("Kafka admin client closed")
