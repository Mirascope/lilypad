#!/bin/bash
# Script to create Kafka topics

KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS:-localhost:9092}"
TOPIC_NAME="${KAFKA_TOPIC_SPAN_INGESTION:-span-ingestion}"

echo "Creating Kafka topics..."
echo "Bootstrap servers: $KAFKA_BOOTSTRAP_SERVERS"
echo "Topic name: $TOPIC_NAME"

echo "Waiting for Kafka to be ready..."
max_attempts=30
attempt=0
while ! kafka-topics --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS" --list &>/dev/null; do
  attempt=$((attempt + 1))
  if [ $attempt -ge $max_attempts ]; then
    echo "Kafka did not become ready in time"
    exit 1
  fi
  echo "Attempt $attempt/$max_attempts: Kafka is not ready yet..."
  sleep 5
done
echo "Kafka is ready!"

echo "Creating topic: $TOPIC_NAME"
kafka-topics \
  --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS" \
  --create \
  --topic "$TOPIC_NAME" \
  --partitions 6 \
  --replication-factor 1 \
  --if-not-exists \
  --config retention.ms=604800000 \
  --config retention.bytes=1073741824

echo "Verifying topic creation..."
kafka-topics \
  --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS" \
  --describe \
  --topic "$TOPIC_NAME"

echo "Topic setup complete!"