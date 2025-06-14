"""Kafka setup service for creating topics on startup."""

import asyncio
import contextlib
import logging
from dataclasses import dataclass

from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import KafkaError, TopicAlreadyExistsError

from lilypad.server.settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class TopicConfig:
    """Configuration for a Kafka topic."""

    name: str
    num_partitions: int = 6
    replication_factor: int = 1
    configs: dict[str, str] | None = None

    def __post_init__(self) -> None:
        if self.configs is None:
            self.configs = {
                "retention.ms": "604800000",  # 7 days
                "retention.bytes": "1073741824",  # 1GB
            }


class KafkaSetupService:
    """Service to setup Kafka topics on application startup."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.admin_client: AIOKafkaAdminClient | None = None

        # Define all topics to be created
        self.topics_to_create = [
            TopicConfig(
                name=self.settings.kafka_topic_span_ingestion,
                num_partitions=6,
                replication_factor=1,
                configs={
                    "retention.ms": "604800000",  # 7 days
                    "retention.bytes": "1073741824",  # 1GB
                },
            ),
            TopicConfig(
                name=self.settings.kafka_topic_stripe_ingestion,  # Add this to your Settings
                num_partitions=6,
                replication_factor=1,
                configs={
                    "retention.ms": "604800000",  # 7 days
                    "retention.bytes": "1073741824",  # 1GB
                },
            ),
            # Add more topics here as needed
        ]

    async def setup_topics(self) -> bool:
        """Create required Kafka topics if they don't exist.

        Returns:
            bool: True if setup successful or skipped, False on error
        """
        # Skip if Kafka is not configured
        if not self.settings.kafka_bootstrap_servers:
            logger.info("Kafka not configured, skipping topic setup")
            return True

        # Skip if auto-setup is disabled
        if not self.settings.kafka_auto_setup_topics:
            logger.info("Kafka auto-setup disabled, skipping topic setup")
            return True

        # Connect to Kafka
        if not await self._connect_to_kafka():
            return False

        try:
            # Create all topics
            success = await self._create_all_topics()

            # Verify all topics
            if success:
                await self._verify_all_topics()

            return success

        except KafkaError as e:
            # Log error but don't fail startup
            logger.error(f"Kafka setup error (non-fatal): {e}")
            return True
        except Exception as e:
            logger.error(
                f"Unexpected error during Kafka setup (non-fatal): {e}", exc_info=True
            )
            return True
        finally:
            if self.admin_client:
                with contextlib.suppress(Exception):
                    await self.admin_client.close()

    async def _connect_to_kafka(self) -> bool:
        """Connect to Kafka with retry logic.

        Returns:
            bool: True if connected successfully, False otherwise
        """
        if not self.settings.kafka_bootstrap_servers:
            logger.error("Kafka bootstrap servers not configured")
            return False

        max_retries = 5
        retry_delay = 2  # Start with 2 seconds

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Connecting to Kafka at {self.settings.kafka_bootstrap_servers} "
                    f"(attempt {attempt + 1}/{max_retries})"
                )

                # Create admin client
                self.admin_client = AIOKafkaAdminClient(
                    bootstrap_servers=self.settings.kafka_bootstrap_servers,
                    client_id="lilypad-setup",
                    request_timeout_ms=30000,
                    connections_max_idle_ms=540000,
                )

                # Start the admin client
                await self.admin_client.start()
                logger.info("Kafka admin client connected successfully")
                return True  # Connection successful

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Failed to connect to Kafka (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {retry_delay} seconds: {e}"
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(
                        f"Failed to connect to Kafka after {max_retries} attempts: {e}"
                    )
                    return False

        return False

    async def _create_all_topics(self) -> bool:
        """Create all configured topics.

        Returns:
            bool: True if all topics created successfully
        """
        if not self.admin_client:
            logger.error("Admin client is not initialized")
            return False

        # Create NewTopic objects for all topics
        new_topics = []
        for topic_config in self.topics_to_create:
            new_topic = NewTopic(
                name=topic_config.name,
                num_partitions=topic_config.num_partitions,
                replication_factor=topic_config.replication_factor,
                topic_configs=topic_config.configs,
            )
            new_topics.append(new_topic)

        # Create topics one by one to handle individual errors
        all_successful = True
        for new_topic in new_topics:
            try:
                logger.info(
                    f"Creating topic '{new_topic.name}' with {new_topic.num_partitions} partitions..."
                )
                await self.admin_client.create_topics([new_topic])
                logger.info(f"Topic '{new_topic.name}' created successfully")

            except TopicAlreadyExistsError:
                logger.info(f"Topic '{new_topic.name}' already exists")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(f"Topic '{new_topic.name}' already exists")
                else:
                    logger.error(f"Failed to create topic '{new_topic.name}': {e}")
                    all_successful = False

        return all_successful

    async def _verify_all_topics(self) -> None:
        """Verify all topics were created successfully."""
        if not self.admin_client:
            return

        # Get list of topic names
        topic_names = [topic.name for topic in self.topics_to_create]

        try:
            # Describe all topics at once
            topic_metadata_list = await self.admin_client.describe_topics(topic_names)

            # Create a set of successfully verified topics
            verified_topics = set()

            for topic_metadata in topic_metadata_list:
                if isinstance(topic_metadata, dict):
                    topic_name = topic_metadata.get("topic")
                    partitions = topic_metadata.get("partitions", [])
                    partition_count = len(partitions)

                    if topic_name in topic_names:
                        logger.info(
                            f"✓ Topic '{topic_name}' confirmed to exist "
                            f"with {partition_count} partitions"
                        )
                        verified_topics.add(topic_name)
                    else:
                        logger.warning(f"⚠ Unexpected topic '{topic_name}' in metadata")

            # Check for any topics that weren't verified
            unverified_topics = set(topic_names) - verified_topics
            for topic_name in unverified_topics:
                logger.warning(
                    f"⚠ Topic '{topic_name}' verification failed - "
                    f"not found in metadata"
                )

        except Exception as e:
            logger.warning(f"Failed to verify topics: {e}")
            # Not critical - topic creation already succeeded or existed
