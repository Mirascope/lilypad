#!/bin/bash
# Script to create Kafka topics for Lilypad development environment

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Lilypad Kafka Topic Setup (Development)${NC}"
echo "========================================"

if ! docker ps | grep -q kafka; then
    echo -e "${RED}Error: Kafka container is not running${NC}"
    echo "Please start the development environment first: make dev"
    exit 1
fi

echo -e "${YELLOW}Waiting for Kafka to be ready...${NC}"
max_attempts=30
attempt=0

while ! docker exec kafka kafka-topics --bootstrap-server localhost:29092 --list &>/dev/null; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo -e "${RED}Error: Kafka did not become ready in time${NC}"
        exit 1
    fi
    echo "Attempt $attempt/$max_attempts: Kafka is not ready yet..."
    sleep 5
done

echo -e "${GREEN}✓ Kafka is ready!${NC}"

echo -e "${YELLOW}Creating span-ingestion topic...${NC}"
if docker exec kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create \
  --topic span-ingestion \
  --partitions 6 \
  --replication-factor 1 \
  --if-not-exists \
  --config retention.ms=604800000 \
  --config retention.bytes=1073741824; then
    echo -e "${GREEN}✓ Topic created successfully${NC}"
else
    echo -e "${RED}✗ Failed to create topic${NC}"
    exit 1
fi

echo -e "${YELLOW}Verifying topic creation...${NC}"
docker exec kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --describe \
  --topic span-ingestion

echo -e "${GREEN}✓ Kafka topic setup complete!${NC}"