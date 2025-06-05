"""Tests for KafkaService."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from aiokafka.errors import KafkaError
from lilypad.server.services.kafka import KafkaService


@pytest.fixture
def kafka_service():
    """Create a KafkaService instance for testing."""
    service = KafkaService()
    # Reset the service state
    service.producer = None
    service._initialized = False
    return service


@pytest.fixture
def mock_settings():
    """Mock settings with Kafka configuration."""
    with patch("lilypad.server.services.kafka.get_settings") as mock:
        settings = MagicMock()
        settings.kafka_bootstrap_servers = "localhost:9092"
        settings.kafka_topic_span_ingestion = "span-ingestion"
        mock.return_value = settings
        yield settings


@pytest.mark.asyncio
async def test_initialize_success():
    """Test successful Kafka initialization."""
    mock_producer = AsyncMock()

    with patch("lilypad.server.services.kafka.get_settings") as mock_get_settings:
        settings = MagicMock()
        settings.kafka_bootstrap_servers = "localhost:9092"
        settings.kafka_topic_span_ingestion = "span-ingestion"
        mock_get_settings.return_value = settings

        kafka_service = KafkaService()

        with patch(
            "lilypad.server.services.kafka.AIOKafkaProducer", return_value=mock_producer
        ):
            result = await kafka_service.initialize()

            assert result is True
            assert kafka_service._initialized is True
            assert kafka_service.producer is mock_producer
            mock_producer.start.assert_called_once()


@pytest.mark.asyncio
async def test_initialize_no_bootstrap_servers(kafka_service):
    """Test initialization when Kafka is not configured."""
    with patch("lilypad.server.services.kafka.get_settings") as mock:
        settings = MagicMock()
        settings.kafka_bootstrap_servers = None
        mock.return_value = settings

        result = await kafka_service.initialize()

        assert result is False
        assert kafka_service._initialized is False
        assert kafka_service.producer is None


@pytest.mark.asyncio
async def test_initialize_failure():
    """Test initialization failure."""
    with patch("lilypad.server.services.kafka.get_settings") as mock_get_settings:
        settings = MagicMock()
        settings.kafka_bootstrap_servers = "localhost:9092"
        settings.kafka_topic_span_ingestion = "span-ingestion"
        mock_get_settings.return_value = settings

        kafka_service = KafkaService()

        with patch(
            "lilypad.server.services.kafka.AIOKafkaProducer"
        ) as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer.start.side_effect = Exception("Connection failed")
            mock_producer_class.return_value = mock_producer

            result = await kafka_service.initialize()

            assert result is False
            assert kafka_service._initialized is False


@pytest.mark.asyncio
async def test_send_span_success(kafka_service, mock_settings):
    """Test successful span sending."""
    mock_producer = AsyncMock()
    mock_metadata = MagicMock()
    mock_metadata.topic = "span-ingestion"
    mock_metadata.partition = 0
    mock_metadata.offset = 123
    mock_producer.send_and_wait.return_value = mock_metadata

    kafka_service.producer = mock_producer
    kafka_service._initialized = True

    span_data = {"trace_id": "trace123", "span_id": "span456", "data": "test"}
    user_id = uuid4()

    result = await kafka_service.send_span(span_data, user_id)

    assert result is True
    mock_producer.send_and_wait.assert_called_once_with(
        topic="span-ingestion", 
        key="trace123", 
        value={**span_data, "user_id": str(user_id)}
    )


@pytest.mark.asyncio
async def test_send_span_not_initialized(kafka_service):
    """Test sending span when Kafka is not initialized."""
    with patch("lilypad.server.services.kafka.get_settings") as mock:
        settings = MagicMock()
        settings.kafka_bootstrap_servers = None
        mock.return_value = settings

        span_data = {"trace_id": "trace123", "span_id": "span456"}
        user_id = uuid4()

        result = await kafka_service.send_span(span_data, user_id)

        assert result is False


@pytest.mark.asyncio
async def test_send_span_kafka_error(kafka_service, mock_settings):
    """Test handling KafkaError during send."""
    mock_producer = AsyncMock()
    mock_producer.send_and_wait.side_effect = KafkaError("Send failed")

    kafka_service.producer = mock_producer
    kafka_service._initialized = True

    span_data = {"trace_id": "trace123", "span_id": "span456"}
    user_id = uuid4()

    result = await kafka_service.send_span(span_data, user_id)

    assert result is False


@pytest.mark.asyncio
async def test_send_spans_batch_success(kafka_service, mock_settings):
    """Test successful batch sending."""
    mock_producer = AsyncMock()
    mock_metadata = MagicMock()
    mock_producer.send_and_wait.return_value = mock_metadata

    kafka_service.producer = mock_producer
    kafka_service._initialized = True

    spans = [
        {"trace_id": "trace1", "span_id": "span1"},
        {"trace_id": "trace2", "span_id": "span2"},
    ]
    user_id = uuid4()

    result = await kafka_service.send_spans_batch(spans, user_id)

    assert result is True
    assert mock_producer.send_and_wait.call_count == 2
    mock_producer.flush.assert_called_once()


@pytest.mark.asyncio
async def test_send_spans_batch_partial_failure(kafka_service, mock_settings):
    """Test partial batch failure."""
    mock_producer = AsyncMock()

    # First send succeeds, second fails
    mock_producer.send_and_wait.side_effect = [
        MagicMock(),  # Success
        KafkaError("Send failed"),  # Failure
    ]

    kafka_service.producer = mock_producer
    kafka_service._initialized = True

    spans = [
        {"trace_id": "trace1", "span_id": "span1"},
        {"trace_id": "trace2", "span_id": "span2"},
    ]
    user_id = uuid4()

    result = await kafka_service.send_spans_batch(spans, user_id)

    assert result is False  # Partial failure
    assert mock_producer.send_and_wait.call_count == 2
    mock_producer.flush.assert_called_once()


@pytest.mark.asyncio
async def test_close(kafka_service):
    """Test closing the Kafka producer."""
    mock_producer = AsyncMock()
    kafka_service.producer = mock_producer
    kafka_service._initialized = True

    await kafka_service.close()

    mock_producer.stop.assert_called_once()
    assert kafka_service.producer is None
    assert kafka_service._initialized is False


@pytest.mark.asyncio
async def test_close_with_error(kafka_service):
    """Test closing with error."""
    mock_producer = AsyncMock()
    mock_producer.stop.side_effect = Exception("Close failed")
    kafka_service.producer = mock_producer
    kafka_service._initialized = True

    # Should not raise exception
    await kafka_service.close()

    assert kafka_service.producer is None
    assert kafka_service._initialized is False


# Test removed - get_kafka_service singleton not used in current implementation