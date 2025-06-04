"""Kafka service for message publishing."""

import json
import logging
from typing import Any

from kafka import KafkaProducer
from kafka.errors import KafkaError

from ..settings import get_settings

logger = logging.getLogger(__name__)


class KafkaService:
    """Service for publishing messages to Kafka topics."""

    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.producer: KafkaProducer | None = None
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize Kafka producer.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        if self._initialized:
            return True

        if not self.settings.kafka_bootstrap_servers:
            logger.info("Kafka not configured, skipping initialization")
            return False

        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.settings.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                compression_type="gzip",
                acks="all",  # Wait for all replicas to acknowledge
                retries=3,
                max_in_flight_requests_per_connection=5,
                request_timeout_ms=30000,
                retry_backoff_ms=100,
            )
            self._initialized = True
            logger.info("Kafka producer initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            return False

    def send_span(self, span_data: dict[str, Any]) -> bool:
        """Send a span to the span ingestion topic.

        Args:
            span_data: Span data dictionary

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self._initialized and not self.initialize():
            logger.warning("Kafka not available, span will be processed synchronously")
            return False

        try:
            # Use trace_id as partition key for ordering within traces
            key = span_data.get("trace_id")

            # Send message asynchronously
            future = self.producer.send(
                topic=self.settings.kafka_topic_span_ingestion, key=key, value=span_data
            )

            # Wait for send to complete (with timeout)
            metadata = future.get(timeout=10)

            logger.debug(
                f"Span sent to Kafka - Topic: {metadata.topic}, "
                f"Partition: {metadata.partition}, Offset: {metadata.offset}"
            )
            return True

        except KafkaError as e:
            logger.error(f"Failed to send span to Kafka: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending span to Kafka: {e}")
            return False

    def send_spans_batch(self, spans: list[dict[str, Any]]) -> bool:
        """Send multiple spans to Kafka in batch.

        Args:
            spans: List of span data dictionaries

        Returns:
            bool: True if all spans sent successfully, False otherwise
        """
        if not self._initialized and not self.initialize():
            logger.warning("Kafka not available, spans will be processed synchronously")
            return False

        success_count = 0

        for span in spans:
            if self.send_span(span):
                success_count += 1

        # Flush to ensure all messages are sent
        try:
            self.producer.flush(timeout=10)
        except KafkaError as e:
            logger.error(f"Error flushing Kafka producer: {e}")

        success = success_count == len(spans)
        if not success:
            logger.warning(
                f"Partial batch send: {success_count}/{len(spans)} spans sent successfully"
            )

        return success

    def close(self) -> None:
        """Close the Kafka producer."""
        if self.producer:
            try:
                self.producer.close()
                logger.info("Kafka producer closed")
            except Exception as e:
                logger.error(f"Error closing Kafka producer: {e}")
            finally:
                self.producer = None
                self._initialized = False
