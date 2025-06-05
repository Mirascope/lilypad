"""Test Kafka connection and verify topic configuration using aiokafka."""

import asyncio
import json
import logging
import os
import sys
import time

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.admin import AIOKafkaAdminClient
from aiokafka.errors import KafkaError

logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger("aiokafka").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def _test_kafka_connection() -> bool:
    """Test basic Kafka connectivity and topic configuration."""
    bootstrap_servers = os.getenv("LILYPAD_KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = os.getenv("LILYPAD_KAFKA_TOPIC_SPAN_INGESTION", "span-ingestion")

    logger.info("Testing Kafka connection to: %s", bootstrap_servers)
    logger.info("Topic: %s", topic)

    # Test admin client
    admin_client = None
    try:
        admin_client = AIOKafkaAdminClient(
            bootstrap_servers=bootstrap_servers, client_id="lilypad-health-check"
        )
        await admin_client.start()

        metadata = await admin_client.describe_cluster()
        if isinstance(metadata, dict):
            logger.info("Cluster metadata: %s", metadata)
        else:
            logger.info("Cluster ID: %s", getattr(metadata, 'cluster_id', 'N/A'))
            logger.info("Controller ID: %s", getattr(metadata, 'controller_id', 'N/A'))

        # Get topic metadata
        topic_metadata = await admin_client.describe_topics([topic])
        
        if topic_metadata and topic_metadata[0].topic == topic:
            topic_info = topic_metadata[0]
            partition_count = len(topic_info.partitions)
            logger.info(
                "✓ Topic '%s' exists with %d partitions", topic, partition_count
            )

            if partition_count != 6:
                logger.warning(
                    "⚠ Warning: Expected 6 partitions but found %d", partition_count
                )
        else:
            logger.error("✗ Topic '%s' does not exist", topic)
            return False

    except Exception as e:
        logger.error("✗ Failed to connect to Kafka admin: %s", e)
        return False
    finally:
        if admin_client:
            await admin_client.close()

    # Test producer
    producer = None
    try:
        producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await producer.start()

        test_message = {
            "test": True,
            "timestamp": time.time(),
            "message": "Health check message",
        }

        record_metadata = await producer.send_and_wait(topic, value=test_message)

        logger.info(
            "✓ Successfully sent test message to partition %d at offset %d",
            record_metadata.partition,
            record_metadata.offset,
        )

    except KafkaError as e:
        logger.error("✗ Failed to send message: %s", e)
        return False
    finally:
        if producer:
            await producer.stop()

    # Test consumer
    consumer = None
    try:
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            auto_offset_reset="latest",
            enable_auto_commit=False,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        await consumer.start()

        logger.info("✓ Successfully created consumer")

    except Exception as e:
        logger.error("✗ Failed to create consumer: %s", e)
        return False
    finally:
        if consumer:
            await consumer.stop()

    logger.info("\n✅ All Kafka health checks passed!")
    return True


async def main() -> None:
    """Main async function."""
    await asyncio.sleep(2)  # Wait for services to be ready
    
    success = await _test_kafka_connection()
    sys.exit(0 if success else 1)


def test_kafka_connection() -> bool:
    """Pytest wrapper for Kafka connection test."""
    import pytest
    pytest.skip("This is a manual test script, not a unit test")
    return True


if __name__ == "__main__":
    asyncio.run(main())