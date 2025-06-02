"""Test Kafka connection and verify topic configuration."""

import json
import logging
import os
import sys
import time

from kafka import KafkaAdminClient, KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError

logging.basicConfig(level=logging.INFO, format='%(message)s')
logging.getLogger('kafka').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def test_kafka_connection() -> bool:
    """Test basic Kafka connectivity and topic configuration."""
    bootstrap_servers = os.getenv('LILYPAD_KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    topic = os.getenv('LILYPAD_KAFKA_TOPIC_SPAN_INGESTION', 'span-ingestion')
    
    logger.info("Testing Kafka connection to: %s", bootstrap_servers)
    logger.info("Topic: %s", topic)
    
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            client_id='lilypad-health-check'
        )
        
        topic_list = admin_client.list_topics()
        logger.info("Available topics: %s", list(topic_list))
        
        if topic in topic_list:
            metadata = admin_client.describe_topics([topic])
            if topic in metadata:
                topic_info = metadata[topic]
                partition_count = len(topic_info.get('partitions', []))
                logger.info("✓ Topic '%s' exists with %d partitions", topic, partition_count)
                
                if partition_count != 6:
                    logger.warning("⚠ Warning: Expected 6 partitions but found %d", partition_count)
        else:
            logger.error("✗ Topic '%s' does not exist", topic)
            return False
            
    except Exception as e:
        logger.error("✗ Failed to connect to Kafka admin: %s", e)
        return False
    
    try:
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        test_message = {
            'test': True,
            'timestamp': time.time(),
            'message': 'Health check message'
        }
        
        future = producer.send(topic, value=test_message)
        record_metadata = future.get(timeout=10)
        
        logger.info("✓ Successfully sent test message to partition %d at offset %d", 
                   record_metadata.partition, record_metadata.offset)
        producer.close()
        
    except KafkaError as e:
        logger.error("✗ Failed to send message: %s", e)
        return False
    
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            auto_offset_reset='latest',
            enable_auto_commit=False,
            consumer_timeout_ms=5000,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        logger.info("✓ Successfully created consumer")
        consumer.close()
        
    except Exception as e:
        logger.error("✗ Failed to create consumer: %s", e)
        return False
    
    logger.info("\n✅ All Kafka health checks passed!")
    return True


if __name__ == "__main__":
    time.sleep(2)
    
    success = test_kafka_connection()
    sys.exit(0 if success else 1)