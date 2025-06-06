"""Base Kafka service for publishing messages to topics."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

from aiokafka.errors import KafkaError

from .kafka_producer import get_kafka_producer

logger = logging.getLogger(__name__)

# Timeout settings
KAFKA_SEND_TIMEOUT_SECONDS = 30
KAFKA_FLUSH_TIMEOUT_SECONDS = 60


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
            logger.warning("Kafka not available - message will not be sent", extra={"topic": self.topic})
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
                timeout=KAFKA_SEND_TIMEOUT_SECONDS
            )
            
            logger.info(
                "Message sent to Kafka",
                extra={
                    "topic": metadata.topic,
                    "partition": metadata.partition,
                    "offset": metadata.offset
                }
            )
            return True
            
        except asyncio.TimeoutError:
            logger.error(
                "Timeout sending message to Kafka",
                extra={"topic": self.topic, "timeout_seconds": KAFKA_SEND_TIMEOUT_SECONDS}
            )
            return False
        except KafkaError as e:
            logger.error("Failed to send message to Kafka", extra={"topic": self.topic, "error": str(e)})
            return False
        except Exception as e:
            logger.error("Unexpected error sending message to Kafka", extra={"error": str(e)})
            return False

    async def send_batch(self, data_list: list[dict[str, Any]]) -> bool:
        """Send multiple messages to Kafka using batch optimization.
        
        Args:
            data_list: List of message data
            
        Returns:
            True if all messages sent successfully, False otherwise
        """
        producer = await get_kafka_producer()
        if not producer:
            logger.warning(
                "Kafka not available - messages will not be sent",
                extra={"topic": self.topic, "message_count": len(data_list)}
            )
            return False
        
        if not data_list:
            return True
        
        # Prepare all messages and send them without waiting
        futures = []
        failed_count = 0
        
        try:
            for data in data_list:
                try:
                    key = self.get_key(data)
                    message = self.transform_message(data)
                    
                    # Send without waiting - producer.send() returns a Future
                    future = producer.send(  # NO await here!
                        topic=self.topic,
                        key=key,
                        value=message,
                    )
                    futures.append(future)
                    
                except Exception as e:
                    logger.error("Failed to prepare message for batch send", extra={"error": str(e)})
                    failed_count += 1
            
            # Wait for all messages to be sent with timeout
            if futures:
                try:
                    await asyncio.wait_for(
                        producer.flush(),
                        timeout=KAFKA_FLUSH_TIMEOUT_SECONDS
                    )
                except asyncio.TimeoutError:
                    logger.error(
                        "Timeout flushing Kafka batch",
                        extra={"timeout_seconds": KAFKA_FLUSH_TIMEOUT_SECONDS}
                    )
                    # Don't know actual failed count on timeout
                    failed_count = len(data_list)  # Conservative estimate
            
        except KafkaError as e:
            logger.error("Kafka batch send error", extra={"error": str(e)})
            failed_count = len(data_list)  # Assume all failed
        
        success_count = len(data_list) - failed_count
        success = failed_count == 0
        
        if success:
            logger.info("Batch sent successfully", extra={"topic": self.topic, "total": len(data_list)})
        else:
            logger.warning(
                "Partial batch send",
                extra={"topic": self.topic, "success": success_count, "total": len(data_list)}
            )
        
        return success
