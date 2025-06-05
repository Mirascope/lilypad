"""Kafka setup service for creating topics on startup."""

import asyncio
import contextlib
import logging

from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import KafkaError, TopicAlreadyExistsError

from lilypad.server.settings import Settings

logger = logging.getLogger(__name__)


class KafkaSetupService:
    """Service to setup Kafka topics on application startup."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.admin_client: AIOKafkaAdminClient | None = None

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

        # Retry logic for Kafka connection
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
                break  # Connection successful, exit retry loop
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Failed to connect to Kafka (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {retry_delay} seconds: {e}"
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to connect to Kafka after {max_retries} attempts: {e}")
                    return False
        
        try:

            # Define topic
            topic = NewTopic(
                name=self.settings.kafka_topic_span_ingestion,
                num_partitions=6,
                replication_factor=1,
                topic_configs={
                    "retention.ms": "604800000",  # 7 days
                    "retention.bytes": "1073741824",  # 1GB
                },
            )

            # Create topic
            try:
                logger.info(f"Creating topic '{self.settings.kafka_topic_span_ingestion}' with 6 partitions...")
                await self.admin_client.create_topics([topic])
                logger.info(
                    f"Topic '{self.settings.kafka_topic_span_ingestion}' created successfully"
                )

            except TopicAlreadyExistsError:
                logger.info(
                    f"Topic '{self.settings.kafka_topic_span_ingestion}' already exists"
                )
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(
                        f"Topic '{self.settings.kafka_topic_span_ingestion}' already exists"
                    )
                else:
                    logger.error(f"Failed to create topic: {e}")
                    raise

            # List topics to verify
            try:
                topics_result = await self.admin_client.describe_topics()
                logger.debug(f"describe_topics returned type: {type(topics_result)}, value: {topics_result}")
                
                # Handle different return types from describe_topics
                topic_names = []
                if isinstance(topics_result, dict):
                    # If it's a dict, it might have topics as values
                    for topic_name, topic_info in topics_result.items():
                        if isinstance(topic_name, str):
                            topic_names.append(topic_name)
                elif isinstance(topics_result, list):
                    # If it's a list of TopicMetadata objects
                    topic_names = [t.topic if hasattr(t, 'topic') else str(t) for t in topics_result]
                else:
                    logger.warning(f"Unexpected type from describe_topics: {type(topics_result)}")
                
                if topic_names:
                    logger.info(f"Available Kafka topics: {topic_names}")
                    if self.settings.kafka_topic_span_ingestion in topic_names:
                        logger.info(f"✓ Topic '{self.settings.kafka_topic_span_ingestion}' confirmed to exist")
                    else:
                        logger.warning(f"⚠ Topic '{self.settings.kafka_topic_span_ingestion}' not found in topic list")
                        
            except Exception as e:
                logger.warning(f"Failed to list topics for verification: {e}")

            return True

        except KafkaError as e:
            # Log error but don't fail startup
            logger.error(f"Kafka setup error (non-fatal): {e}")
            return True
        except Exception as e:
            logger.error(f"Unexpected error during Kafka setup (non-fatal): {e}", exc_info=True)
            return True
        finally:
            if self.admin_client:
                with contextlib.suppress(Exception):
                    await self.admin_client.close()
