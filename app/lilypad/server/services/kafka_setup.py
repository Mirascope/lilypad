"""Kafka setup service for creating topics on startup."""

import contextlib
import logging

from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import KafkaError, TopicAlreadyExistsError
from lilypad.server.settings import Settings

logger = logging.getLogger(__name__)


class KafkaSetupService:
    """Service to setup Kafka topics on application startup."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.admin_client: KafkaAdminClient | None = None

    def setup_topics(self) -> bool:
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

        try:
            logger.info(
                f"Connecting to Kafka at {self.settings.kafka_bootstrap_servers}"
            )

            # Create admin client with connection timeout
            self.admin_client = KafkaAdminClient(
                bootstrap_servers=self.settings.kafka_bootstrap_servers,
                client_id="lilypad-setup",
                request_timeout_ms=30000,
                connections_max_idle_ms=60000,  # 60 seconds
                api_version_auto_timeout_ms=10000,  # 10 seconds for version check
            )

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
                fs = self.admin_client.create_topics([topic], validate_only=False)
                for topic_name, f in fs.items():
                    try:
                        f.result()  # Wait for operation to complete
                        logger.info(f"Topic '{topic_name}' created successfully")
                    except Exception as e:
                        logger.error(f"Failed to create topic '{topic_name}': {e}")
                        return False

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
                    raise

            return True

        except KafkaError as e:
            # Log error but don't fail startup
            logger.warning(f"Kafka setup error (non-fatal): {e}")
            return True
        except Exception as e:
            logger.warning(f"Unexpected error during Kafka setup (non-fatal): {e}")
            return True
        finally:
            if self.admin_client:
                with contextlib.suppress(Exception):
                    self.admin_client.close()
