"""Base Kafka service for publishing messages to topics."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

from aiokafka.errors import KafkaError

from .kafka_producer import get_kafka_producer

logger = logging.getLogger(__name__)

# Timeout settings
KAFKA_SEND_TIMEOUT_SECONDS = 10  # Reduced from 30s for faster failure detection
KAFKA_FLUSH_TIMEOUT_SECONDS = 30  # Reduced from 60s

# Batch processing settings
MAX_BATCH_SIZE = 500  # Reduced from 1000 for better memory management


class BaseKafkaService(ABC):
    """Abstract base class for Kafka services.

    This provides the core functionality for sending messages to Kafka.
    Subclasses should implement topic, get_key, and transform_message methods.
    """

    @property
    @abstractmethod
    def topic(self) -> str:
        """The Kafka topic to publish to."""
        pass

    def get_key(self, data: dict[str, Any]) -> str | None:
        """Extract the partition key from message data.

        Override this method to provide custom key extraction logic.
        Default implementation returns None (round-robin partitioning).
        """
        return None

    def transform_message(self, data: dict[str, Any]) -> dict[str, Any]:
        """Transform the message before sending.

        Override this method to add fields or modify the message.
        Default implementation returns the message unchanged.
        """
        return data

    async def send(self, data: dict[str, Any]) -> bool:
        """Send a single message to Kafka.

        Args:
            data: The message data

        Returns:
            True if sent successfully, False otherwise
        """
        producer = await get_kafka_producer()
        if not producer:
            logger.warning(
                "Kafka not available - message will not be sent",
                extra={"topic": self.topic},
            )
            return False

        try:
            key = self.get_key(data)
            message = self.transform_message(data)

            # Send with timeout
            metadata = await asyncio.wait_for(
                producer.send_and_wait(
                    topic=self.topic,
                    key=key,
                    value=message,
                ),
                timeout=KAFKA_SEND_TIMEOUT_SECONDS,
            )

            logger.info(
                "Message sent to Kafka",
                extra={
                    "topic": metadata.topic,
                    "partition": metadata.partition,
                    "offset": metadata.offset,
                },
            )
            return True

        except asyncio.TimeoutError:
            logger.error(
                "Timeout sending message to Kafka",
                extra={
                    "topic": self.topic,
                    "timeout_seconds": KAFKA_SEND_TIMEOUT_SECONDS,
                },
            )
            return False
        except KafkaError as e:
            logger.error(
                "Failed to send message to Kafka",
                extra={"topic": self.topic, "error": str(e)},
            )
            return False
        except Exception as e:
            logger.error(
                "Unexpected error sending message to Kafka", extra={"error": str(e)}
            )
            return False

    async def send_batch(self, data_list: list[dict[str, Any]]) -> bool:
        """Send multiple messages to Kafka using batch optimization with memory-efficient chunking.

        Args:
            data_list: List of message data

        Returns:
            True if all messages sent successfully, False otherwise
        """
        producer = await get_kafka_producer()
        if not producer:
            logger.warning(
                "Kafka not available - messages will not be sent",
                extra={"topic": self.topic, "message_count": len(data_list)},
            )
            return False

        if not data_list:
            return True

        total_failed = 0
        total_messages = len(data_list)

        # Process in chunks to avoid memory accumulation
        for chunk_start in range(0, total_messages, MAX_BATCH_SIZE):
            chunk_end = min(chunk_start + MAX_BATCH_SIZE, total_messages)
            chunk = data_list[chunk_start:chunk_end]

            futures = []
            chunk_failed = 0

            try:
                # Send messages in this chunk
                for data in chunk:
                    try:
                        key = self.get_key(data)
                        message = self.transform_message(data)

                        # Send without waiting - producer.send() returns a Future
                        future = producer.send(
                            topic=self.topic,
                            key=key,
                            value=message,
                        )
                        futures.append(future)

                    except Exception as e:
                        logger.error(
                            "Failed to prepare message for batch send",
                            extra={"error": str(e)},
                        )
                        chunk_failed += 1

                # Wait for all futures in this chunk to complete
                if futures:
                    try:
                        # Wait for all send operations to complete
                        results = await asyncio.wait_for(
                            asyncio.gather(*futures, return_exceptions=True),
                            timeout=KAFKA_FLUSH_TIMEOUT_SECONDS,
                        )

                        # Count failures
                        for result in results:
                            if isinstance(result, Exception):
                                chunk_failed += 1
                                logger.error(
                                    "Message send failed", extra={"error": str(result)}
                                )

                    except asyncio.TimeoutError:
                        logger.error(
                            "Timeout waiting for Kafka sends",
                            extra={
                                "timeout_seconds": KAFKA_FLUSH_TIMEOUT_SECONDS,
                                "chunk_start": chunk_start,
                                "chunk_size": len(chunk),
                            },
                        )
                        # Assume all remaining futures failed on timeout
                        chunk_failed += len(futures)

            except KafkaError as e:
                logger.error(
                    "Kafka chunk send error",
                    extra={"error": str(e), "chunk_start": chunk_start},
                )
                chunk_failed = len(chunk)  # Assume all in chunk failed

            total_failed += chunk_failed

            # Log progress for large batches
            if total_messages > MAX_BATCH_SIZE:
                logger.info(
                    "Batch progress",
                    extra={
                        "topic": self.topic,
                        "processed": chunk_end,
                        "total": total_messages,
                        "failed_so_far": total_failed,
                    },
                )

        success_count = total_messages - total_failed
        success = total_failed == 0

        if success:
            logger.info(
                "Batch sent successfully",
                extra={"topic": self.topic, "total": total_messages},
            )
        else:
            logger.warning(
                "Partial batch send",
                extra={
                    "topic": self.topic,
                    "success": success_count,
                    "total": total_messages,
                },
            )

        return success
