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


class TestKafkaProducer:
    """Test cases for Kafka producer singleton."""

    @pytest.mark.asyncio
    async def test_get_kafka_producer_not_configured(self):
        """Test that None is returned when Kafka is not configured."""
        with patch("lilypad.server.services.kafka_producer.get_settings") as mock:
            mock_settings = MagicMock()
            mock_settings.kafka_bootstrap_servers = None
            mock.return_value = mock_settings

            producer = await get_kafka_producer()
            assert producer is None

    @pytest.mark.asyncio
    async def test_get_kafka_producer_invalid_servers(self):
        """Test that None is returned with invalid server configuration."""
        with patch("lilypad.server.services.kafka_producer.get_settings") as mock:
            mock_settings = MagicMock()
            mock_settings.kafka_bootstrap_servers = "invalid-server"  # Missing port
            mock.return_value = mock_settings

            producer = await get_kafka_producer()
            assert producer is None

    @pytest.mark.asyncio
    async def test_get_kafka_producer_success(self, mock_settings):
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
    async def test_get_kafka_producer_retry_on_failure(self, mock_settings):
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
    async def test_close_kafka_producer(self):
        """Test closing the Kafka producer."""
        mock_producer = AsyncMock()

        import lilypad.server.services.kafka_producer as producer_module

        producer_module._producer_instance = mock_producer
        producer_module._producer_lock = asyncio.Lock()

        await close_kafka_producer()

        mock_producer.stop.assert_called_once()
        assert producer_module._producer_instance is None
        assert producer_module._producer_lock is None


class TestBaseKafkaService:
    """Test cases for base Kafka service."""

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
    async def test_send_no_producer(self):
        """Test send when producer is not available."""
        service = self.ConcreteKafkaService()

        with patch("lilypad.server.services.kafka_base.get_kafka_producer") as mock:
            mock.return_value = None

            result = await service.send({"id": "test-1", "data": "value"})
            assert result is False

    @pytest.mark.asyncio
    async def test_send_success(self):
        """Test successful message send."""
        service = self.ConcreteKafkaService()

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
    async def test_send_timeout(self):
        """Test send timeout handling."""
        service = self.ConcreteKafkaService()

        mock_producer = AsyncMock()
        mock_producer.send_and_wait.side_effect = asyncio.TimeoutError()

        with patch("lilypad.server.services.kafka_base.get_kafka_producer") as mock:
            mock.return_value = mock_producer

            result = await service.send({"id": "test-1", "data": "value"})
            assert result is False

    @pytest.mark.asyncio
    async def test_send_kafka_error(self):
        """Test Kafka error handling."""
        service = self.ConcreteKafkaService()

        mock_producer = AsyncMock()
        mock_producer.send_and_wait.side_effect = KafkaError("Kafka error")

        with patch("lilypad.server.services.kafka_base.get_kafka_producer") as mock:
            mock.return_value = mock_producer

            result = await service.send({"id": "test-1", "data": "value"})
            assert result is False

    @pytest.mark.asyncio
    async def test_send_batch_empty(self):
        """Test sending empty batch."""
        service = self.ConcreteKafkaService()

        with patch("lilypad.server.services.kafka_base.get_kafka_producer") as mock:
            mock.return_value = AsyncMock()

            result = await service.send_batch([])
            assert result is True

    @pytest.mark.asyncio
    async def test_send_batch_success(self):
        """Test successful batch send."""
        service = self.ConcreteKafkaService()

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
    async def test_send_batch_chunking(self):
        """Test batch chunking for large batches."""
        service = self.ConcreteKafkaService()

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
                messages = [
                    {"id": f"test-{i}", "data": f"value-{i}"} for i in range(12)
                ]

                result = await service.send_batch(messages)
                assert result is True
                assert mock_producer.send.call_count == 12
                # Should be called 3 times (chunks of 5, 5, 2)
                assert mock_producer.flush.call_count == 3


class TestSpanKafkaService:
    """Test cases for span Kafka service."""

    @pytest.mark.asyncio
    async def test_init(self, mock_user, mock_settings):
        """Test service initialization."""
        with patch("lilypad.server.services.span_kafka_service.get_settings") as mock:
            mock.return_value = mock_settings

            service = SpanKafkaService(mock_user)
            assert service.user == mock_user
            assert service.topic == "span-ingestion"

    def test_get_key(self, mock_user, mock_settings):
        """Test key extraction."""
        with patch("lilypad.server.services.span_kafka_service.get_settings") as mock:
            mock.return_value = mock_settings

            service = SpanKafkaService(mock_user)
            data = {"trace_id": "trace-123", "span_id": "span-456"}

            key = service.get_key(data)
            assert key == "trace-123"

    def test_transform_message_success(self, mock_user, mock_settings):
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

    def test_transform_message_missing_trace_id(self, mock_user, mock_settings):
        """Test validation for missing trace_id."""
        with patch("lilypad.server.services.span_kafka_service.get_settings") as mock:
            mock.return_value = mock_settings

            service = SpanKafkaService(mock_user)
            data = {"span_id": "span-456", "name": "test span"}

            with pytest.raises(ValueError, match="Missing required field: trace_id"):
                service.transform_message(data)

    def test_transform_message_not_dict(self, mock_user, mock_settings):
        """Test validation for non-dict data."""
        with patch("lilypad.server.services.span_kafka_service.get_settings") as mock:
            mock.return_value = mock_settings

            service = SpanKafkaService(mock_user)

            with pytest.raises(ValueError, match="Span data must be a dictionary"):
                service.transform_message("not a dict")  # type: ignore[arg-type]

    def test_transform_message_long_string(self, mock_user, mock_settings):
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

    def test_transform_message_missing_user(self, mock_settings):
        """Test validation for missing user context."""
        with patch("lilypad.server.services.span_kafka_service.get_settings") as mock:
            mock.return_value = mock_settings

            service = SpanKafkaService(None)  # type: ignore[arg-type]
            data = {"trace_id": "trace-123"}

            with pytest.raises(ValueError, match="User context is missing"):
                service.transform_message(data)

    def test_transform_message_circular_reference(self, mock_user, mock_settings):
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

    def test_transform_message_too_large(self, mock_user, mock_settings):
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
    async def test_get_span_kafka_service(self, mock_user):
        """Test dependency injection helper."""
        with patch("lilypad.server.services.span_kafka_service.get_settings"):
            service = await get_span_kafka_service(mock_user)
            assert isinstance(service, SpanKafkaService)
            assert service.user == mock_user
