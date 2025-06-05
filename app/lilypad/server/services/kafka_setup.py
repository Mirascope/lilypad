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

            # Verify the specific topic exists
            try:
                # Describe the specific topic we just created
                topic_metadata_list = await self.admin_client.describe_topics([self.settings.kafka_topic_span_ingestion])
                
                if topic_metadata_list and len(topic_metadata_list) > 0:
                    topic_metadata = topic_metadata_list[0]
                    
                    # Handle dict response (aiokafka returns dicts, not objects)
                    if isinstance(topic_metadata, dict):
                        topic_name = topic_metadata.get('topic')
                        partitions = topic_metadata.get('partitions', [])
                        partition_count = len(partitions)
                        
                        if topic_name == self.settings.kafka_topic_span_ingestion:
                            logger.info(
                                f"✓ Topic '{self.settings.kafka_topic_span_ingestion}' confirmed to exist "
                                f"with {partition_count} partitions"
                            )
                        else:
                            logger.warning(
                                f"⚠ Topic metadata returned but name doesn't match: "
                                f"expected '{self.settings.kafka_topic_span_ingestion}', got '{topic_name}'"
                            )
                    else:
                        # Fallback for object-based response (if aiokafka changes in future)
                        if hasattr(topic_metadata, 'topic') and topic_metadata.topic == self.settings.kafka_topic_span_ingestion:
                            partition_count = len(topic_metadata.partitions) if hasattr(topic_metadata, 'partitions') else 0
                            logger.info(
                                f"✓ Topic '{self.settings.kafka_topic_span_ingestion}' confirmed to exist "
                                f"with {partition_count} partitions"
                            )
                        else:
                            logger.warning(
                                "⚠ Topic metadata returned but doesn't match expected format"
                            )
                else:
                    logger.warning(
                        f"⚠ Topic '{self.settings.kafka_topic_span_ingestion}' verification failed - "
                        f"no metadata returned"
                    )
                        
            except Exception as e:
                logger.warning(f"Failed to verify topic: {e}")
                # Not critical - topic creation already succeeded or existed

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
