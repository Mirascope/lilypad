"""Kafka producer singleton for managing connections."""

import asyncio
import contextlib
import json
import logging
import threading
from typing import Any

from aiokafka import AIOKafkaProducer

from ..settings import get_settings

logger = logging.getLogger(__name__)

# Singleton instance
_producer_instance: AIOKafkaProducer | None = None
_producer_lock: asyncio.Lock | None = None
_lock_creation_lock = threading.Lock()  # Thread-safe lock creation
_is_closing = False  # Flag to prevent new connections during shutdown


# Serialization function (avoid lambda overhead)
def _serialize_value(v: dict[str, Any]) -> bytes:
    """Serialize value to JSON bytes."""
    return json.dumps(v, default=str, check_circular=True).encode("utf-8")


def _serialize_key(k: str | None) -> bytes | None:
    """Serialize key to bytes."""
    return k.encode("utf-8") if k else None


async def get_kafka_producer() -> AIOKafkaProducer | None:
    """Get or create the singleton Kafka producer instance.

    Returns:
        The Kafka producer instance, or None if Kafka is not configured
    """
    global _producer_instance, _producer_lock, _is_closing

    # Don't create new instances during shutdown
    if _is_closing:
        logger.warning("Kafka producer is shutting down, not creating new instance")
        return None

    if _producer_instance is not None:
        # Check if producer is still healthy using public API
        try:
            # Try to check if client is ready (non-blocking check)
            client = getattr(_producer_instance, "client", None)
            if client and hasattr(client, "ready"):
                await asyncio.wait_for(client.ready(), timeout=0.1)
                return _producer_instance
            else:
                # If we can't verify health, recreate
                logger.warning("Cannot verify Kafka producer health, recreating...")
                _producer_instance = None
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(
                "Kafka producer health check failed, recreating...",
                extra={"error": str(e)},
            )
            _producer_instance = None

    # Thread-safe lock creation
    if _producer_lock is None:
        with _lock_creation_lock:
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

        # Validate bootstrap servers format
        try:
            servers = settings.kafka_bootstrap_servers.split(",")
            for server in servers:
                if ":" not in server:
                    raise ValueError(f"Invalid server format (missing port): {server}")
        except Exception as e:
            logger.error(
                "Invalid kafka_bootstrap_servers configuration", extra={"error": str(e)}
            )
            return None

        logger.info("Initializing Kafka producer")

        # Retry logic for initialization
        max_retries = 3
        retry_delay = 1
        max_retry_delay = 30  # Cap retry delay

        for attempt in range(max_retries):
            producer = None
            try:
                logger.info(f"Attempt {attempt + 1}/{max_retries}: Creating producer")
                producer = AIOKafkaProducer(
                    bootstrap_servers=settings.kafka_bootstrap_servers,
                    value_serializer=_serialize_value,
                    key_serializer=_serialize_key,
                    compression_type="gzip",  # Universally supported compression
                    acks=1,  # Only wait for leader acknowledgment (faster)
                    linger_ms=10,  # Wait up to 10ms for batching
                    max_batch_size=16384,  # 16KB batch size
                    max_request_size=1048576,  # 1MB
                    request_timeout_ms=30000,
                    retry_backoff_ms=1000,  # 1 second retry backoff
                    connections_max_idle_ms=540000,
                    # Reduce metadata refresh interval to prevent hanging tasks
                    metadata_max_age_ms=300000,  # 5 minutes
                    # Note: enable_idempotence requires acks='all', so we don't use it
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
                        logger.error(
                            "Error cleaning up producer",
                            extra={"error": str(cleanup_error)},
                        )
                    finally:
                        # Ensure resources are freed
                        producer = None

                if attempt < max_retries - 1:
                    logger.warning(
                        f"Failed to initialize Kafka producer (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {retry_delay} seconds",
                        extra={"error": str(e)},
                    )
                    await asyncio.sleep(retry_delay)
                    # Exponential backoff with cap
                    retry_delay = min(retry_delay * 2, max_retry_delay)
                else:
                    logger.error(
                        f"Failed to initialize Kafka producer after {max_retries} attempts",
                        extra={"error": str(e)},
                    )
                    return None

        return None


async def close_kafka_producer() -> None:
    """Close the Kafka producer if it exists."""
    global _producer_instance, _producer_lock, _is_closing

    # Set closing flag to prevent new connections
    _is_closing = True

    # Use lock to ensure thread-safe closure
    if _producer_lock:
        async with _producer_lock:
            if _producer_instance:
                try:
                    # First, flush any pending messages with a timeout
                    logger.info("Flushing pending Kafka messages before shutdown...")
                    try:
                        await asyncio.wait_for(_producer_instance.flush(), timeout=5.0)
                        logger.info("Kafka producer flushed successfully")
                    except asyncio.TimeoutError:
                        logger.warning("Timeout while flushing Kafka producer (5s)")

                    # Stop the producer - this should clean up all internal tasks
                    logger.info("Stopping Kafka producer...")
                    await _producer_instance.stop()

                    # Give a small delay for internal tasks to clean up
                    await asyncio.sleep(0.1)

                    logger.info("Kafka producer closed successfully")
                except Exception as e:
                    logger.error(
                        "Error closing Kafka producer", extra={"error": str(e)}
                    )
                finally:
                    _producer_instance = None
    else:
        # If no lock exists, just clean up
        if _producer_instance:
            try:
                # Try to flush before stopping
                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(_producer_instance.flush(), timeout=5.0)
                await _producer_instance.stop()
                # Give a small delay for internal tasks to clean up
                await asyncio.sleep(0.1)
            except Exception:
                pass  # Suppress all exceptions during cleanup
            finally:
                _producer_instance = None

    # Clear the lock as well
    _producer_lock = None

    # Reset closing flag (in case of restart)
    _is_closing = False
