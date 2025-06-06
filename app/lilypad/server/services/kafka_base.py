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
            logger.warning(f"Kafka not available - message will not be sent to {self.topic}")
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
                f"Message sent to Kafka - Topic: {metadata.topic}, "
                f"Partition: {metadata.partition}, Offset: {metadata.offset}"
            )
            return True
            
        except asyncio.TimeoutError:
            logger.error(
                f"Timeout sending message to Kafka topic {self.topic} "
                f"(timeout: {KAFKA_SEND_TIMEOUT_SECONDS}s)"
            )
            return False
        except KafkaError as e:
            logger.error(f"Failed to send message to Kafka topic {self.topic}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message to Kafka: {e}")
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
                f"Kafka not available - {len(data_list)} messages will not be sent to {self.topic}"
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
                    
                    # Send without waiting (async operation)
                    future = await producer.send(
                        topic=self.topic,
                        key=key,
                        value=message,
                    )
                    futures.append(future)
                    
                except Exception as e:
                    logger.error(f"Failed to prepare message for batch send: {e}")
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
                        f"Timeout flushing Kafka batch "
                        f"(timeout: {KAFKA_FLUSH_TIMEOUT_SECONDS}s)"
                    )
                    failed_count = len(futures)  # Assume all failed on timeout
                
                # Check results
                for future in futures:
                    try:
                        # This will raise if the send failed
                        await future
                    except Exception as e:
                        logger.error(f"Message failed in batch: {e}")
                        failed_count += 1
            
        except KafkaError as e:
            logger.error(f"Kafka batch send error: {e}")
            failed_count = len(data_list)  # Assume all failed
        
        success_count = len(data_list) - failed_count
        success = failed_count == 0
        
        if success:
            logger.info(f"Batch sent successfully - Total: {len(data_list)} messages to {self.topic}")
        else:
            logger.warning(
                f"Partial batch send - Success: {success_count}/{len(data_list)} messages to {self.topic}"
            )
        
        return success
