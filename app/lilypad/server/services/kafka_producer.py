"""Kafka producer singleton for managing connections."""

import asyncio
import json
import logging

from aiokafka import AIOKafkaProducer

from ..settings import get_settings

logger = logging.getLogger(__name__)

# Singleton instance
_producer_instance: AIOKafkaProducer | None = None
_producer_lock: asyncio.Lock | None = None


async def get_kafka_producer() -> AIOKafkaProducer | None:
    """Get or create the singleton Kafka producer instance.
    
    Returns:
        The Kafka producer instance, or None if Kafka is not configured
    """
    global _producer_instance, _producer_lock
    
    if _producer_instance is not None:
        # Check if producer is still healthy
        try:
            if _producer_instance._closed:
                logger.warning("Kafka producer was closed, recreating...")
                _producer_instance = None
            else:
                return _producer_instance
        except Exception:
            # If we can't check status, assume it's broken
            logger.warning("Cannot check Kafka producer status, recreating...")
            _producer_instance = None
    
    # Create lock on first use (when event loop exists)
    if _producer_lock is None:
        _producer_lock = asyncio.Lock()
    
    async with _producer_lock:
        # Double-check pattern
        if _producer_instance is not None:
            return _producer_instance
        
        settings = get_settings()
        
        if not settings.kafka_bootstrap_servers:
            logger.info("Kafka not configured, skipping initialization")
            return None
        
        logger.info("Initializing Kafka producer")
        
        # Retry logic for initialization
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            producer = None
            try:
                logger.info(f"Attempt {attempt + 1}/{max_retries}: Creating producer")
                producer = AIOKafkaProducer(
                    bootstrap_servers=settings.kafka_bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v, default=str, check_circular=True).encode("utf-8"),
                    key_serializer=lambda k: k.encode("utf-8") if k else None,
                    compression_type="gzip",
                    acks=1,  # Only wait for leader acknowledgment
                    linger_ms=10,  # Wait up to 10ms for batching
                    max_batch_size=16384,  # 16KB batch size
                    max_request_size=1048576,  # 1MB
                    request_timeout_ms=30000,
                    retry_backoff_ms=100,
                    connections_max_idle_ms=540000,
                )
                
                await producer.start()
                _producer_instance = producer
                logger.info("Kafka producer initialized successfully")
                return producer
                
            except Exception as e:
                # Clean up partially initialized producer
                if producer:
                    try:
                        await producer.stop()
                    except Exception as cleanup_error:
                        logger.error("Error cleaning up producer", extra={"error": str(cleanup_error)})
                
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Failed to initialize Kafka producer (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {retry_delay} seconds",
                        extra={"error": str(e)}
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(
                        f"Failed to initialize Kafka producer after {max_retries} attempts",
                        extra={"error": str(e)}
                    )
                    return None
        
        return None


async def close_kafka_producer() -> None:
    """Close the Kafka producer if it exists."""
    global _producer_instance
    
    if _producer_instance:
        try:
            await _producer_instance.stop()
            logger.info("Kafka producer closed")
        except Exception as e:
            logger.error("Error closing Kafka producer", extra={"error": str(e)})
        finally:
            _producer_instance = None