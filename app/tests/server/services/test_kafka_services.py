"""Unit tests for Kafka services."""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import UUID

import pytest
from aiokafka.errors import KafkaError

from lilypad.server.schemas.users import UserPublic
from lilypad.server.services.kafka_base import BaseKafkaService
from lilypad.server.services.kafka_producer import (
    close_kafka_producer,
    get_kafka_producer,
)
from lilypad.server.services.span_kafka_service import (
    SpanKafkaService,
    get_span_kafka_service,
)


@pytest.fixture
def mock_user():
    """Create a mock user."""
    return UserPublic(
        uuid=UUID("123e4567-e89b-12d3-a456-426614174000"),
        email="test@example.com",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock()
    settings.kafka_bootstrap_servers = "localhost:9092"
    settings.kafka_topic_span_ingestion = "span-ingestion"
    return settings


@pytest.mark.asyncio
async def test_get_kafka_producer_not_configured():
    """Test that None is returned when Kafka is not configured."""
    with patch("lilypad.server.services.kafka_producer.get_settings") as mock:
        mock_settings = MagicMock()
        mock_settings.kafka_bootstrap_servers = None
        mock.return_value = mock_settings

        producer = await get_kafka_producer()
        assert producer is None


@pytest.mark.asyncio
async def test_get_kafka_producer_invalid_servers():
    """Test that None is returned with invalid server configuration."""
    with patch("lilypad.server.services.kafka_producer.get_settings") as mock:
        mock_settings = MagicMock()
        mock_settings.kafka_bootstrap_servers = "invalid-server"  # Missing port
        mock.return_value = mock_settings

        producer = await get_kafka_producer()
        assert producer is None


@pytest.mark.asyncio
async def test_get_kafka_producer_success(mock_settings):
    """Test successful producer creation."""
    with patch(
        "lilypad.server.services.kafka_producer.get_settings"
    ) as mock_get_settings:
        mock_get_settings.return_value = mock_settings

        with patch(
            "lilypad.server.services.kafka_producer.AIOKafkaProducer"
        ) as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer

            # Reset singleton state
            import lilypad.server.services.kafka_producer as producer_module

            producer_module._producer_instance = None
            producer_module._producer_lock = None

            producer = await get_kafka_producer()

            assert producer is not None
            assert producer == mock_producer
            mock_producer.start.assert_called_once()


@pytest.mark.asyncio
async def test_get_kafka_producer_retry_on_failure(mock_settings):
    """Test retry logic when producer initialization fails."""
    with patch(
        "lilypad.server.services.kafka_producer.get_settings"
    ) as mock_get_settings:
        mock_get_settings.return_value = mock_settings

        with patch(
            "lilypad.server.services.kafka_producer.AIOKafkaProducer"
        ) as mock_producer_class:
            # First attempt fails, second succeeds
            mock_producer = AsyncMock()
            mock_producer_class.side_effect = [
                Exception("Connection failed"),
                mock_producer,
            ]

            # Reset singleton state
            import lilypad.server.services.kafka_producer as producer_module

            producer_module._producer_instance = None
            producer_module._producer_lock = None

            with patch("asyncio.sleep", new_callable=AsyncMock):
                producer = await get_kafka_producer()

                assert producer is not None
                assert mock_producer_class.call_count == 2


@pytest.mark.asyncio
async def test_close_kafka_producer():
    """Test closing the Kafka producer."""
    mock_producer = AsyncMock()

    import lilypad.server.services.kafka_producer as producer_module

    producer_module._producer_instance = mock_producer
    producer_module._producer_lock = asyncio.Lock()

    await close_kafka_producer()

    mock_producer.stop.assert_called_once()
    assert producer_module._producer_instance is None
    assert producer_module._producer_lock is None


class ConcreteKafkaService(BaseKafkaService):
    """Concrete implementation for testing."""

    @property
    def topic(self) -> str:
        """Return the test topic name."""
        return "test-topic"

    def get_key(self, data: dict[str, Any]) -> str | None:
        """Extract id as the partition key."""
        return data.get("id")

    def transform_message(self, data: dict[str, Any]) -> dict[str, Any]:
        """Add a transformed flag to the message."""
        return {**data, "transformed": True}


@pytest.mark.asyncio
async def test_base_kafka_send_no_producer():
    """Test send when producer is not available."""
    service = ConcreteKafkaService()

    with patch("lilypad.server.services.kafka_base.get_kafka_producer") as mock:
        mock.return_value = None

        result = await service.send({"id": "test-1", "data": "value"})
        assert result is False


@pytest.mark.asyncio
async def test_base_kafka_send_success():
    """Test successful message send."""
    service = ConcreteKafkaService()

    mock_producer = AsyncMock()
    mock_metadata = MagicMock()
    mock_metadata.topic = "test-topic"
    mock_metadata.partition = 0
    mock_metadata.offset = 100
    mock_producer.send_and_wait.return_value = mock_metadata

    with patch("lilypad.server.services.kafka_base.get_kafka_producer") as mock:
        mock.return_value = mock_producer

        result = await service.send({"id": "test-1", "data": "value"})
        assert result is True

        mock_producer.send_and_wait.assert_called_once_with(
            topic="test-topic",
            key="test-1",
            value={"id": "test-1", "data": "value", "transformed": True},
        )


@pytest.mark.asyncio
async def test_base_kafka_send_timeout():
    """Test send timeout handling."""
    service = ConcreteKafkaService()

    mock_producer = AsyncMock()
    mock_producer.send_and_wait.side_effect = asyncio.TimeoutError()

    with patch("lilypad.server.services.kafka_base.get_kafka_producer") as mock:
        mock.return_value = mock_producer

        result = await service.send({"id": "test-1", "data": "value"})
        assert result is False


@pytest.mark.asyncio
async def test_base_kafka_send_kafka_error():
    """Test Kafka error handling."""
    service = ConcreteKafkaService()

    mock_producer = AsyncMock()
    mock_producer.send_and_wait.side_effect = KafkaError("Kafka error")

    with patch("lilypad.server.services.kafka_base.get_kafka_producer") as mock:
        mock.return_value = mock_producer

        result = await service.send({"id": "test-1", "data": "value"})
        assert result is False


@pytest.mark.asyncio
async def test_base_kafka_send_batch_empty():
    """Test sending empty batch."""
    service = ConcreteKafkaService()

    with patch("lilypad.server.services.kafka_base.get_kafka_producer") as mock:
        mock.return_value = AsyncMock()

        result = await service.send_batch([])
        assert result is True


@pytest.mark.asyncio
async def test_base_kafka_send_batch_success():
    """Test successful batch send."""
    service = ConcreteKafkaService()

    mock_producer = Mock()
    # Create a mock future that can be awaited
    mock_future = asyncio.Future()
    mock_future.set_result(None)
    mock_producer.send = Mock(return_value=mock_future)
    mock_producer.flush = AsyncMock()

    with patch("lilypad.server.services.kafka_base.get_kafka_producer") as mock:
        mock.return_value = mock_producer

        messages = [{"id": f"test-{i}", "data": f"value-{i}"} for i in range(10)]

        result = await service.send_batch(messages)
        assert result is True
        assert mock_producer.send.call_count == 10
        mock_producer.flush.assert_called()


@pytest.mark.asyncio
async def test_base_kafka_send_batch_chunking():
    """Test batch chunking for large batches."""
    service = ConcreteKafkaService()

    mock_producer = Mock()
    # Create a mock future that can be awaited
    mock_future = asyncio.Future()
    mock_future.set_result(None)
    mock_producer.send = Mock(return_value=mock_future)
    mock_producer.flush = AsyncMock()

    with patch("lilypad.server.services.kafka_base.get_kafka_producer") as mock:
        mock.return_value = mock_producer

        # Create more messages than MAX_BATCH_SIZE
        with patch("lilypad.server.services.kafka_base.MAX_BATCH_SIZE", 5):
            messages = [{"id": f"test-{i}", "data": f"value-{i}"} for i in range(12)]

            result = await service.send_batch(messages)
            assert result is True
            assert mock_producer.send.call_count == 12
            # Should be called 3 times (chunks of 5, 5, 2)
            assert mock_producer.flush.call_count == 3


@pytest.mark.asyncio
async def test_span_kafka_init(mock_user, mock_settings):
    """Test service initialization."""
    with patch("lilypad.server.services.span_kafka_service.get_settings") as mock:
        mock.return_value = mock_settings

        service = SpanKafkaService(mock_user)
        assert service.user == mock_user
        assert service.topic == "span-ingestion"


def test_span_kafka_get_key(mock_user, mock_settings):
    """Test key extraction."""
    with patch("lilypad.server.services.span_kafka_service.get_settings") as mock:
        mock.return_value = mock_settings

        service = SpanKafkaService(mock_user)
        data = {"trace_id": "trace-123", "span_id": "span-456"}

        key = service.get_key(data)
        assert key == "trace-123"


def test_span_kafka_transform_message_success(mock_user, mock_settings):
    """Test successful message transformation."""
    with patch("lilypad.server.services.span_kafka_service.get_settings") as mock:
        mock.return_value = mock_settings

        service = SpanKafkaService(mock_user)
        data = {
            "trace_id": "trace-123",
            "span_id": "span-456",
            "name": "test span",
        }

        transformed = service.transform_message(data)
        assert "user_id" in transformed
        assert transformed["user_id"] == str(mock_user.uuid)
        assert transformed["trace_id"] == "trace-123"


def test_span_kafka_transform_message_missing_trace_id(mock_user, mock_settings):
    """Test validation for missing trace_id."""
    with patch("lilypad.server.services.span_kafka_service.get_settings") as mock:
        mock.return_value = mock_settings

        service = SpanKafkaService(mock_user)
        data = {"span_id": "span-456", "name": "test span"}

        with pytest.raises(ValueError, match="Missing required field: trace_id"):
            service.transform_message(data)


def test_span_kafka_transform_message_not_dict(mock_user, mock_settings):
    """Test validation for non-dict data."""
    with patch("lilypad.server.services.span_kafka_service.get_settings") as mock:
        mock.return_value = mock_settings

        service = SpanKafkaService(mock_user)

        with pytest.raises(ValueError, match="Span data must be a dictionary"):
            service.transform_message("not a dict")  # type: ignore[arg-type]


def test_span_kafka_transform_message_long_string(mock_user, mock_settings):
    """Test validation for oversized string fields."""
    with patch("lilypad.server.services.span_kafka_service.get_settings") as mock:
        mock.return_value = mock_settings

        service = SpanKafkaService(mock_user)
        data = {
            "trace_id": "trace-123",
            "huge_field": "x" * 10001,  # Over 10KB
        }

        with pytest.raises(ValueError, match="String field exceeds maximum length"):
            service.transform_message(data)


def test_span_kafka_transform_message_missing_user(mock_settings):
    """Test validation for missing user context."""
    with patch("lilypad.server.services.span_kafka_service.get_settings") as mock:
        mock.return_value = mock_settings

        service = SpanKafkaService(None)  # type: ignore[arg-type]
        data = {"trace_id": "trace-123"}

        with pytest.raises(ValueError, match="User context is missing"):
            service.transform_message(data)


def test_span_kafka_transform_message_circular_reference(mock_user, mock_settings):
    """Test validation for circular references."""
    with patch("lilypad.server.services.span_kafka_service.get_settings") as mock:
        mock.return_value = mock_settings

        service = SpanKafkaService(mock_user)
        data = {"trace_id": "trace-123"}
        data["self"] = data  # type: ignore[assignment]  # Create circular reference

        with pytest.raises(
            ValueError,
            match="Circular reference detected|Message contains circular references",
        ):
            service.transform_message(data)


def test_span_kafka_transform_message_too_large(mock_user, mock_settings):
    """Test validation for oversized messages."""
    with patch("lilypad.server.services.span_kafka_service.get_settings") as mock:
        mock.return_value = mock_settings

        service = SpanKafkaService(mock_user)
        # Create a message that will be too large
        data = {
            "trace_id": "trace-123",
            **{f"field_{i}": "x" * 1000 for i in range(1500)},  # Many large fields
        }

        with pytest.raises(ValueError, match="Message too large"):
            service.transform_message(data)


@pytest.mark.asyncio
async def test_get_span_kafka_service(mock_user):
    """Test dependency injection helper."""
    with patch("lilypad.server.services.span_kafka_service.get_settings"):
        service = await get_span_kafka_service(mock_user)
        assert isinstance(service, SpanKafkaService)
        assert service.user == mock_user


class DefaultKafkaService(BaseKafkaService):
    """Service that uses default implementations."""

    @property
    def topic(self) -> str:
        """Return the test topic name."""
        return "default-topic"


def test_base_kafka_default_get_key():
    """Test default get_key implementation returns None."""
    service = DefaultKafkaService()
    result = service.get_key({"id": "test-1", "data": "value"})
    assert result is None


def test_base_kafka_default_transform_message():
    """Test default transform_message implementation returns data unchanged."""
    service = DefaultKafkaService()
    data = {"id": "test-1", "data": "value"}
    result = service.transform_message(data)
    assert result == data


@pytest.mark.asyncio
async def test_base_kafka_send_unexpected_error():
    """Test unexpected error handling in send."""
    service = ConcreteKafkaService()

    mock_producer = AsyncMock()
    mock_producer.send_and_wait.side_effect = RuntimeError("Unexpected error")

    with patch("lilypad.server.services.kafka_base.get_kafka_producer") as mock:
        mock.return_value = mock_producer

        result = await service.send({"id": "test-1", "data": "value"})
        assert result is False


@pytest.mark.asyncio
async def test_base_kafka_send_batch_no_producer():
    """Test batch send when producer is not available."""
    service = ConcreteKafkaService()

    with patch("lilypad.server.services.kafka_base.get_kafka_producer") as mock:
        mock.return_value = None

        result = await service.send_batch([{"id": "test-1", "data": "value"}])
        assert result is False


@pytest.mark.asyncio
async def test_base_kafka_send_batch_message_preparation_error():
    """Test error during message preparation in batch send."""
    service = ConcreteKafkaService()

    # Create a service that throws exception in transform_message
    class ErrorKafkaService(BaseKafkaService):
        @property
        def topic(self) -> str:
            return "error-topic"

        def transform_message(self, data: dict[str, Any]) -> dict[str, Any]:
            """Raise error to test exception handling."""
            raise ValueError("Transform error")

    error_service = ErrorKafkaService()

    mock_producer = Mock()
    mock_producer.flush = AsyncMock()

    with patch("lilypad.server.services.kafka_base.get_kafka_producer") as mock:
        mock.return_value = mock_producer

        result = await error_service.send_batch([{"id": "test-1", "data": "value"}])
        assert result is False


@pytest.mark.asyncio
async def test_base_kafka_send_batch_future_exception():
    """Test exception handling when futures fail in batch send."""
    service = ConcreteKafkaService()

    mock_producer = Mock()
    # Create futures that will raise exceptions
    failed_future = asyncio.Future()
    failed_future.set_exception(KafkaError("Send failed"))
    mock_producer.send = Mock(return_value=failed_future)
    mock_producer.flush = AsyncMock()

    with patch("lilypad.server.services.kafka_base.get_kafka_producer") as mock:
        mock.return_value = mock_producer

        result = await service.send_batch([{"id": "test-1", "data": "value"}])
        assert result is False


@pytest.mark.asyncio
async def test_base_kafka_send_batch_timeout_during_flush():
    """Test timeout during flush operation in batch send."""
    service = ConcreteKafkaService()

    mock_producer = Mock()
    mock_future = asyncio.Future()
    mock_future.set_result(None)
    mock_producer.send = Mock(return_value=mock_future)
    mock_producer.flush = AsyncMock(side_effect=asyncio.TimeoutError())

    with patch("lilypad.server.services.kafka_base.get_kafka_producer") as mock:
        mock.return_value = mock_producer

        result = await service.send_batch([{"id": "test-1", "data": "value"}])
        assert result is True  # Still returns True as the send succeeded


@pytest.mark.asyncio
async def test_base_kafka_send_batch_timeout_waiting_for_sends():
    """Test timeout waiting for send operations in batch."""
    service = ConcreteKafkaService()

    mock_producer = Mock()
    # Create a future that will never complete
    hanging_future = asyncio.Future()
    mock_producer.send = Mock(return_value=hanging_future)
    mock_producer.flush = AsyncMock()

    with patch("lilypad.server.services.kafka_base.get_kafka_producer") as mock:
        mock.return_value = mock_producer

        # Patch asyncio.wait_for to simulate timeout
        with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
            result = await service.send_batch([{"id": "test-1", "data": "value"}])
            assert result is False


@pytest.mark.asyncio
async def test_base_kafka_send_batch_kafka_error():
    """Test KafkaError handling in batch send."""
    service = ConcreteKafkaService()

    mock_producer = Mock()
    mock_producer.flush = AsyncMock()

    with patch("lilypad.server.services.kafka_base.get_kafka_producer") as mock:
        mock.return_value = mock_producer

        # Mock the entire try block to raise KafkaError
        with patch.object(service, "get_key", side_effect=KafkaError("Kafka error")):
            result = await service.send_batch([{"id": "test-1", "data": "value"}])
            assert result is False


@pytest.mark.asyncio
async def test_base_kafka_send_batch_partial_failure():
    """Test partial batch failure to trigger warning log."""
    service = ConcreteKafkaService()

    mock_producer = Mock()
    # First future succeeds, second fails
    success_future = asyncio.Future()
    success_future.set_result(None)
    failed_future = asyncio.Future()
    failed_future.set_exception(KafkaError("Send failed"))
    
    mock_producer.send = Mock(side_effect=[success_future, failed_future])
    mock_producer.flush = AsyncMock()

    with patch("lilypad.server.services.kafka_base.get_kafka_producer") as mock:
        mock.return_value = mock_producer

        result = await service.send_batch([
            {"id": "test-1", "data": "value1"},
            {"id": "test-2", "data": "value2"}
        ])
        assert result is False  # Should fail due to partial failure


def test_serialize_value():
    """Test _serialize_value function."""
    from lilypad.server.services.kafka_producer import _serialize_value
    
    data = {"test": "value", "number": 42}
    result = _serialize_value(data)
    assert isinstance(result, bytes)
    assert b"test" in result


def test_serialize_key():
    """Test _serialize_key function."""
    from lilypad.server.services.kafka_producer import _serialize_key
    
    # Test with string key
    result = _serialize_key("test-key")
    assert result == b"test-key"
    
    # Test with None key
    result = _serialize_key(None)
    assert result is None


@pytest.mark.asyncio
async def test_get_kafka_producer_closing_flag():
    """Test get_kafka_producer when closing flag is set."""
    import lilypad.server.services.kafka_producer as producer_module
    
    # Set closing flag
    producer_module._is_closing = True
    
    with patch("lilypad.server.services.kafka_producer.logger") as mock_logger:
        result = await get_kafka_producer()
    
    assert result is None
    mock_logger.warning.assert_called_once()
    
    # Reset flag
    producer_module._is_closing = False


@pytest.mark.asyncio
async def test_get_kafka_producer_double_check_pattern():
    """Test get_kafka_producer double-check pattern."""
    import lilypad.server.services.kafka_producer as producer_module
    
    # Reset singleton state
    producer_module._producer_instance = None
    producer_module._producer_lock = None
    
    mock_producer = AsyncMock()
    
    with (
        patch("lilypad.server.services.kafka_producer.get_settings") as mock_get_settings,
        patch("lilypad.server.services.kafka_producer.AIOKafkaProducer", return_value=mock_producer)
    ):
        mock_settings = MagicMock()
        mock_settings.kafka_bootstrap_servers = "localhost:9092"
        mock_get_settings.return_value = mock_settings
        
        # First call should create producer
        producer1 = await get_kafka_producer()
        
        # Set the instance manually to test double-check
        producer_module._producer_instance = mock_producer
        
        # Second call should return existing instance (hitting line 60)
        producer2 = await get_kafka_producer()
        
        assert producer1 == producer2
        assert producer1 == mock_producer


@pytest.mark.asyncio
async def test_get_kafka_producer_cleanup_error():
    """Test get_kafka_producer handles cleanup errors."""
    import lilypad.server.services.kafka_producer as producer_module
    
    # Reset singleton state
    producer_module._producer_instance = None
    producer_module._producer_lock = None
    
    mock_producer = AsyncMock()
    mock_producer.start.side_effect = Exception("Start failed")
    mock_producer.stop.side_effect = Exception("Stop failed")
    
    with (
        patch("lilypad.server.services.kafka_producer.get_settings") as mock_get_settings,
        patch("lilypad.server.services.kafka_producer.AIOKafkaProducer", return_value=mock_producer),
        patch("lilypad.server.services.kafka_producer.logger") as mock_logger,
        patch("asyncio.sleep", new_callable=AsyncMock)
    ):
        mock_settings = MagicMock()
        mock_settings.kafka_bootstrap_servers = "localhost:9092"
        mock_get_settings.return_value = mock_settings
        
        result = await get_kafka_producer()
        
        assert result is None
        # Should log cleanup error
        mock_logger.error.assert_called()


@pytest.mark.asyncio
async def test_get_kafka_producer_fallback_return():
    """Test get_kafka_producer fallback return paths."""
    import lilypad.server.services.kafka_producer as producer_module
    
    # Reset singleton state
    producer_module._producer_instance = None
    producer_module._producer_lock = None
    
    with (
        patch("lilypad.server.services.kafka_producer.get_settings") as mock_get_settings,
        patch("lilypad.server.services.kafka_producer.AIOKafkaProducer", side_effect=Exception("Always fails")),
        patch("asyncio.sleep", new_callable=AsyncMock),
        patch("lilypad.server.services.kafka_producer.logger")
    ):
        mock_settings = MagicMock()
        mock_settings.kafka_bootstrap_servers = "localhost:9092"
        mock_get_settings.return_value = mock_settings
        
        result = await get_kafka_producer()
        
        # Should hit the fallback return None at line 145
        assert result is None


@pytest.mark.asyncio
async def test_close_kafka_producer_timeout_flush():
    """Test close_kafka_producer handles flush timeout."""
    import lilypad.server.services.kafka_producer as producer_module
    
    mock_producer = AsyncMock()
    mock_producer.flush.side_effect = asyncio.TimeoutError()
    
    # Set up producer instance
    producer_module._producer_instance = mock_producer
    producer_module._producer_lock = asyncio.Lock()
    
    with (
        patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()),
        patch("lilypad.server.services.kafka_producer.logger") as mock_logger,
        patch("asyncio.sleep", new_callable=AsyncMock)
    ):
        await close_kafka_producer()
    
    # Should log timeout warning
    mock_logger.warning.assert_called_with("Timeout while flushing Kafka producer (5s)")


@pytest.mark.asyncio
async def test_close_kafka_producer_no_lock():
    """Test close_kafka_producer when no lock exists."""
    import lilypad.server.services.kafka_producer as producer_module
    
    mock_producer = AsyncMock()
    
    # Set up producer instance without lock
    producer_module._producer_instance = mock_producer
    producer_module._producer_lock = None
    
    with patch("asyncio.sleep", new_callable=AsyncMock):
        await close_kafka_producer()
    
    # Should still close the producer (hitting lines 166-167)
    mock_producer.stop.assert_called_once()


@pytest.mark.asyncio
async def test_close_kafka_producer_error():
    """Test close_kafka_producer handles errors during closure."""
    import lilypad.server.services.kafka_producer as producer_module
    
    mock_producer = AsyncMock()
    mock_producer.stop.side_effect = Exception("Stop failed")
    
    # Set up producer instance
    producer_module._producer_instance = mock_producer
    producer_module._producer_lock = asyncio.Lock()
    
    with (
        patch("lilypad.server.services.kafka_producer.logger") as mock_logger,
        patch("asyncio.sleep", new_callable=AsyncMock)
    ):
        await close_kafka_producer()
    
    # Should log error
    mock_logger.error.assert_called_with("Error closing Kafka producer", extra={"error": "Stop failed"})
