"""Kafka service for message publishing."""

import asyncio
import json
import logging
from typing import Any
from uuid import UUID

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from ..settings import get_settings

logger = logging.getLogger(__name__)


# Singleton instance
_kafka_service_instance: "KafkaService | None" = None


class KafkaService:
    """Service for publishing messages to Kafka topics."""

    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.producer: AIOKafkaProducer | None = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize Kafka producer with retry logic.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        if self._initialized:
            return True

        if not self.settings.kafka_bootstrap_servers:
            logger.info("Kafka not configured, skipping initialization")
            return False

        # Retry logic for Kafka initialization
        max_retries = 3
        retry_delay = 1  # Start with 1 second
        
        for attempt in range(max_retries):
            try:
                self.producer = AIOKafkaProducer(
                    bootstrap_servers=self.settings.kafka_bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    key_serializer=lambda k: k.encode("utf-8") if k else None,
                    compression_type="gzip",
                    acks="all",  # Wait for all replicas to acknowledge
                    max_request_size=1048576,  # 1MB
                    request_timeout_ms=30000,
                    retry_backoff_ms=100,
                    connections_max_idle_ms=540000,
                )
                await self.producer.start()
                self._initialized = True
                logger.info("Kafka producer initialized successfully")
                return True

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Failed to initialize Kafka producer (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {retry_delay} seconds: {e}"
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to initialize Kafka producer after {max_retries} attempts: {e}")
                    return False
        
        return False

    async def send_span(self, span_data: dict[str, Any], user_id: UUID) -> bool:
        """Send a span to the span ingestion topic.

        Args:
            span_data: Span data dictionary
            user_id: User ID associated with the span

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self._initialized and not await self.initialize():
            logger.warning("Kafka not available, span will be processed synchronously")
            return False

        try:
            # Use trace_id as partition key for ordering within traces
            key = span_data.get("trace_id")

            # Send message asynchronously
            metadata = await self.producer.send_and_wait(  # pyright: ignore [reportOptionalMemberAccess]
                topic=self.settings.kafka_topic_span_ingestion,
                key=key,
                value={**span_data, "user_id": str(user_id)},
            )

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

    async def send_spans_batch(
        self, spans: list[dict[str, Any]], user_id: UUID
    ) -> bool:
        """Send multiple spans to Kafka in batch.

        Args:
            spans: List of span data dictionaries
            user_id: User ID associated with the spans

        Returns:
            bool: True if all spans sent successfully, False otherwise
        """
        if not self._initialized and not await self.initialize():
            logger.warning("Kafka not available, spans will be processed synchronously")
            return False

        success_count = 0

        for span in spans:
            if await self.send_span(span, user_id):
                success_count += 1

        # Flush to ensure all messages are sent
        try:
            await self.producer.flush()  # pyright: ignore [reportOptionalMemberAccess]
        except KafkaError as e:
            logger.error(f"Error flushing Kafka producer: {e}")

        success = success_count == len(spans)
        if not success:
            logger.warning(
                f"Partial batch send: {success_count}/{len(spans)} spans sent successfully"
            )

        return success

    async def close(self) -> None:
        """Close the Kafka producer."""
        if self.producer:
            try:
                await self.producer.stop()
                logger.info("Kafka producer closed")
            except Exception as e:
                logger.error(f"Error closing Kafka producer: {e}")
            finally:
                self.producer = None
                self._initialized = False


def get_kafka_service() -> KafkaService:
    """Get or create the singleton KafkaService instance."""
    global _kafka_service_instance
    if _kafka_service_instance is None:
        _kafka_service_instance = KafkaService()
    return _kafka_service_instance
