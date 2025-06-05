"""Tests for KafkaService."""

from unittest.mock import MagicMock, patch

import pytest

from kafka.errors import KafkaError
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


def test_initialize_success():
    """Test successful Kafka initialization."""
    mock_producer = MagicMock()

    with patch("lilypad.server.services.kafka.get_settings") as mock_get_settings:
        settings = MagicMock()
        settings.kafka_bootstrap_servers = "localhost:9092"
        settings.kafka_topic_span_ingestion = "span-ingestion"
        mock_get_settings.return_value = settings

        kafka_service = KafkaService()

        with patch(
            "lilypad.server.services.kafka.KafkaProducer", return_value=mock_producer
        ):
            result = kafka_service.initialize()

            assert result is True
            assert kafka_service._initialized is True
            assert kafka_service.producer is mock_producer


def test_initialize_no_bootstrap_servers(kafka_service):
    """Test initialization when Kafka is not configured."""
    with patch("lilypad.server.services.kafka.get_settings") as mock:
        settings = MagicMock()
        settings.kafka_bootstrap_servers = None
        mock.return_value = settings

        result = kafka_service.initialize()

        assert result is False
        assert kafka_service._initialized is False
        assert kafka_service.producer is None


def test_initialize_failure():
    """Test initialization failure."""
    with patch("lilypad.server.services.kafka.get_settings") as mock_get_settings:
        settings = MagicMock()
        settings.kafka_bootstrap_servers = "localhost:9092"
        settings.kafka_topic_span_ingestion = "span-ingestion"
        mock_get_settings.return_value = settings

        kafka_service = KafkaService()

        with patch(
            "lilypad.server.services.kafka.KafkaProducer"
        ) as mock_producer_class:
            mock_producer_class.side_effect = Exception("Connection failed")

            result = kafka_service.initialize()

            assert result is False
            assert kafka_service._initialized is False


def test_send_span_success(kafka_service, mock_settings):
    """Test successful span sending."""
    mock_producer = MagicMock()
    mock_future = MagicMock()
    mock_metadata = MagicMock()
    mock_metadata.topic = "span-ingestion"
    mock_metadata.partition = 0
    mock_metadata.offset = 123
    mock_future.get.return_value = mock_metadata
    mock_producer.send.return_value = mock_future

    kafka_service.producer = mock_producer
    kafka_service._initialized = True

    span_data = {"trace_id": "trace123", "span_id": "span456", "data": "test"}

    result = kafka_service.send_span(span_data)

    assert result is True
    mock_producer.send.assert_called_once_with(
        topic="span-ingestion", key="trace123", value=span_data
    )


def test_send_span_not_initialized(kafka_service):
    """Test sending span when Kafka is not initialized."""
    with patch("lilypad.server.services.kafka.get_settings") as mock:
        settings = MagicMock()
        settings.kafka_bootstrap_servers = None
        mock.return_value = settings

        span_data = {"trace_id": "trace123", "span_id": "span456"}

        result = kafka_service.send_span(span_data)

        assert result is False


def test_send_span_kafka_error(kafka_service, mock_settings):
    """Test handling KafkaError during send."""
    mock_producer = MagicMock()
    mock_future = MagicMock()
    mock_future.get.side_effect = KafkaError("Send failed")
    mock_producer.send.return_value = mock_future

    kafka_service.producer = mock_producer
    kafka_service._initialized = True

    span_data = {"trace_id": "trace123", "span_id": "span456"}

    result = kafka_service.send_span(span_data)

    assert result is False


def test_send_spans_batch_success(kafka_service, mock_settings):
    """Test successful batch sending."""
    mock_producer = MagicMock()
    mock_future = MagicMock()
    mock_metadata = MagicMock()
    mock_future.get.return_value = mock_metadata
    mock_producer.send.return_value = mock_future

    kafka_service.producer = mock_producer
    kafka_service._initialized = True

    spans = [
        {"trace_id": "trace1", "span_id": "span1"},
        {"trace_id": "trace2", "span_id": "span2"},
    ]

    result = kafka_service.send_spans_batch(spans)

    assert result is True
    assert mock_producer.send.call_count == 2
    mock_producer.flush.assert_called_once()


def test_send_spans_batch_partial_failure(kafka_service, mock_settings):
    """Test partial batch failure."""
    mock_producer = MagicMock()

    # Create different futures for each call
    mock_future1 = MagicMock()
    mock_future1.get.return_value = MagicMock()  # Success

    mock_future2 = MagicMock()
    mock_future2.get.side_effect = KafkaError("Send failed")  # Failure

    # First send succeeds, second fails
    mock_producer.send.side_effect = [mock_future1, mock_future2]

    kafka_service.producer = mock_producer
    kafka_service._initialized = True

    spans = [
        {"trace_id": "trace1", "span_id": "span1"},
        {"trace_id": "trace2", "span_id": "span2"},
    ]

    result = kafka_service.send_spans_batch(spans)

    assert result is False  # Partial failure
    assert mock_producer.send.call_count == 2
    mock_producer.flush.assert_called_once()


def test_close(kafka_service):
    """Test closing the Kafka producer."""
    mock_producer = MagicMock()
    kafka_service.producer = mock_producer
    kafka_service._initialized = True

    kafka_service.close()

    mock_producer.close.assert_called_once()
    assert kafka_service.producer is None
    assert kafka_service._initialized is False


def test_close_with_error(kafka_service):
    """Test closing with error."""
    mock_producer = MagicMock()
    mock_producer.close.side_effect = Exception("Close failed")
    kafka_service.producer = mock_producer
    kafka_service._initialized = True

    # Should not raise exception
    kafka_service.close()

    assert kafka_service.producer is None
    assert kafka_service._initialized is False


# Test removed - get_kafka_service singleton not used in current implementation
