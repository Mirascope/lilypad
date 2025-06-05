"""Tests for SpanQueueProcessor."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from lilypad.server.services.span_queue_processor import (
    SpanQueueProcessor,
    TraceBuffer,
    get_span_queue_processor,
)


@pytest.fixture
def trace_buffer():
    """Create a TraceBuffer instance for testing."""
    return TraceBuffer("trace123")


@pytest.fixture
def processor():
    """Create a SpanQueueProcessor instance for testing."""
    return SpanQueueProcessor()


@pytest.fixture
def mock_settings():
    """Mock settings for queue processor."""
    with patch("lilypad.server.services.span_queue_processor.get_settings") as mock:
        settings = MagicMock()
        settings.kafka_bootstrap_servers = "localhost:9092"
        settings.kafka_topic_span_ingestion = "span-ingestion"
        settings.kafka_consumer_group = "test-consumer"
        settings.kafka_max_concurrent_traces = 1000
        settings.kafka_max_spans_per_trace = 500
        settings.kafka_buffer_ttl_seconds = 300
        settings.kafka_cleanup_interval_seconds = 60
        settings.stripe_api_key = None
        mock.return_value = settings
        yield settings


class TestTraceBuffer:
    """Tests for TraceBuffer class."""

    def test_add_span(self, trace_buffer):
        """Test adding spans to buffer."""
        span1 = {"span_id": "span1", "data": "test1"}
        span2 = {"span_id": "span2", "data": "test2"}

        trace_buffer.add_span(span1)
        trace_buffer.add_span(span2)

        assert len(trace_buffer.spans) == 2
        assert trace_buffer.spans["span1"] == span1
        assert trace_buffer.spans["span2"] == span2

    def test_span_ids(self, trace_buffer):
        """Test getting span IDs."""
        trace_buffer.add_span({"span_id": "span1"})
        trace_buffer.add_span({"span_id": "span2"})

        span_ids = trace_buffer.span_ids

        assert span_ids == {"span1", "span2"}

    def test_is_complete_no_dependencies(self, trace_buffer):
        """Test completeness check with no dependencies."""
        trace_buffer.add_span({"span_id": "span1", "parent_span_id": None})
        trace_buffer.add_span({"span_id": "span2", "parent_span_id": None})

        assert trace_buffer.is_complete() is True

    def test_is_complete_with_satisfied_dependencies(self, trace_buffer):
        """Test completeness check with satisfied dependencies."""
        trace_buffer.add_span({"span_id": "parent", "parent_span_id": None})
        trace_buffer.add_span({"span_id": "child", "parent_span_id": "parent"})

        assert trace_buffer.is_complete() is True

    def test_is_complete_with_missing_parent(self, trace_buffer):
        """Test completeness check with missing parent."""
        trace_buffer.add_span({"span_id": "child", "parent_span_id": "parent"})

        assert trace_buffer.is_complete() is False

    def test_get_dependency_order_simple(self, trace_buffer):
        """Test dependency ordering with simple hierarchy."""
        parent = {"span_id": "parent", "parent_span_id": None}
        child = {"span_id": "child", "parent_span_id": "parent"}

        trace_buffer.add_span(child)  # Add child first
        trace_buffer.add_span(parent)

        ordered = trace_buffer.get_dependency_order()

        assert len(ordered) == 2
        assert ordered[0]["span_id"] == "parent"
        assert ordered[1]["span_id"] == "child"

    def test_get_dependency_order_complex(self, trace_buffer):
        """Test dependency ordering with complex hierarchy."""
        root = {"span_id": "root", "parent_span_id": None}
        child1 = {"span_id": "child1", "parent_span_id": "root"}
        child2 = {"span_id": "child2", "parent_span_id": "root"}
        grandchild = {"span_id": "grandchild", "parent_span_id": "child1"}

        # Add in random order
        trace_buffer.add_span(grandchild)
        trace_buffer.add_span(child2)
        trace_buffer.add_span(root)
        trace_buffer.add_span(child1)

        ordered = trace_buffer.get_dependency_order()

        assert len(ordered) == 4
        assert ordered[0]["span_id"] == "root"
        # Children should come after root, grandchild after child1
        span_ids = [s["span_id"] for s in ordered]
        assert span_ids.index("root") < span_ids.index("child1")
        assert span_ids.index("root") < span_ids.index("child2")
        assert span_ids.index("child1") < span_ids.index("grandchild")


class TestSpanQueueProcessor:
    """Tests for SpanQueueProcessor class."""

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful initialization."""
        mock_consumer = AsyncMock()

        with patch(
            "lilypad.server.services.span_queue_processor.get_settings"
        ) as mock_get_settings:
            settings = MagicMock()
            settings.kafka_bootstrap_servers = "localhost:9092"
            settings.kafka_topic_span_ingestion = "span-ingestion"
            settings.kafka_consumer_group = "test-consumer"
            mock_get_settings.return_value = settings

            processor = SpanQueueProcessor()

            with patch(
                "lilypad.server.services.span_queue_processor.AIOKafkaConsumer",
                return_value=mock_consumer,
            ):
                result = await processor.initialize()

                assert result is True
                assert processor.consumer is mock_consumer
                mock_consumer.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_no_kafka(self, processor):
        """Test initialization when Kafka is not configured."""
        with patch("lilypad.server.services.span_queue_processor.get_settings") as mock:
            settings = MagicMock()
            settings.kafka_bootstrap_servers = None
            mock.return_value = settings

            result = await processor.initialize()

            assert result is False
            assert processor.consumer is None

    @pytest.mark.asyncio
    async def test_process_message_complete_trace(self, processor, mock_settings):
        """Test processing a message that completes a trace."""
        # Setup
        processor._running = True

        # Mock the process_trace method
        processor._process_trace = AsyncMock()

        # Create message
        parent_span = {
            "trace_id": "trace123",
            "span_id": "parent",
            "parent_span_id": None,
            "attributes": {"lilypad.project.uuid": str(uuid4())},
        }

        mock_record = MagicMock()
        mock_record.value = parent_span

        # Add child span to buffer first
        processor.trace_buffers["trace123"] = TraceBuffer("trace123")
        processor.trace_buffers["trace123"].add_span(
            {"trace_id": "trace123", "span_id": "child", "parent_span_id": "parent"}
        )

        # Process parent span
        await processor._process_message(mock_record)

        # Should complete the trace
        processor._process_trace.assert_called_once_with("trace123")

    @pytest.mark.asyncio
    async def test_process_message_incomplete_trace(self, processor, mock_settings):
        """Test processing a message that doesn't complete a trace."""
        processor._running = True
        processor._process_trace = AsyncMock()

        # Create child span message (parent missing)
        child_span = {
            "trace_id": "trace123",
            "span_id": "child",
            "parent_span_id": "parent",  # Parent doesn't exist yet
            "attributes": {"lilypad.project.uuid": str(uuid4())},
        }

        mock_record = MagicMock()
        mock_record.value = child_span

        await processor._process_message(mock_record)

        # Should not process trace yet
        processor._process_trace.assert_not_called()
        assert "trace123" in processor.trace_buffers

    @pytest.mark.asyncio
    async def test_process_message_max_spans_limit(self, processor, mock_settings):
        """Test processing when max spans per trace is exceeded."""
        processor._running = True
        processor._process_trace = AsyncMock()
        mock_settings.kafka_max_spans_per_trace = 2

        # Create buffer with 2 spans already
        processor.trace_buffers["trace123"] = TraceBuffer("trace123")
        processor.trace_buffers["trace123"].add_span({"span_id": "span1"})
        processor.trace_buffers["trace123"].add_span({"span_id": "span2"})

        # Try to add third span
        new_span = {
            "trace_id": "trace123",
            "span_id": "span3",
            "attributes": {"lilypad.project.uuid": str(uuid4())},
        }

        mock_record = MagicMock()
        mock_record.value = new_span

        await processor._process_message(mock_record)

        # Should process trace due to limit
        processor._process_trace.assert_called_once_with("trace123")

    @pytest.mark.asyncio
    async def test_force_process_incomplete_trace(self, processor):
        """Test force processing an incomplete trace."""
        processor._process_trace = AsyncMock()

        # Create incomplete trace
        buffer = TraceBuffer("trace123")
        buffer.add_span({"span_id": "child", "parent_span_id": "missing_parent"})
        processor.trace_buffers["trace123"] = buffer

        await processor._force_process_incomplete_trace("trace123")

        # Parent should be set to None
        assert buffer.spans["child"]["parent_span_id"] is None
        processor._process_trace.assert_called_once_with("trace123")

    @pytest.mark.asyncio
    async def test_cleanup_incomplete_traces(self):
        """Test cleanup of timed-out traces."""
        with patch(
            "lilypad.server.services.span_queue_processor.get_settings"
        ) as mock_get_settings:
            settings = MagicMock()
            settings.kafka_bootstrap_servers = "localhost:9092"
            settings.kafka_buffer_ttl_seconds = 0.1  # 0.1 second TTL
            settings.kafka_cleanup_interval_seconds = 0.05  # Fast cleanup
            mock_get_settings.return_value = settings

            processor = SpanQueueProcessor()
            processor._running = True
            processor._force_process_incomplete_trace = AsyncMock()

            # Create old trace
            old_buffer = TraceBuffer("old_trace")
            old_buffer.created_at = time.time() - 1  # 1 second old
            processor.trace_buffers["old_trace"] = old_buffer

            # Create new trace
            new_buffer = TraceBuffer("new_trace")
            processor.trace_buffers["new_trace"] = new_buffer

            # Run cleanup in a task
            cleanup_task = asyncio.create_task(processor._cleanup_incomplete_traces())
            await asyncio.sleep(0.1)  # Let it run one iteration
            processor._running = False
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass

            # Only old trace should be processed
            processor._force_process_incomplete_trace.assert_called_with("old_trace")

    def test_convert_to_span_create(self, processor):
        """Test converting span data to SpanCreate object."""
        span_data = {
            "span_id": "span123",
            "parent_span_id": "parent123",
            "cost": 0.5,
            "input_tokens": 100,
            "output_tokens": 50,
            "duration_ms": 1000,
            "scope": "llm",
            "attributes": {
                "lilypad.type": "function",  # Use valid SpanType
                "lilypad.function.uuid": str(uuid4()),
            },
        }

        span_create = processor._convert_to_span_create(span_data)

        assert span_create.span_id == "span123"
        assert span_create.parent_span_id == "parent123"
        assert span_create.cost == 0.5
        assert span_create.input_tokens == 100
        assert span_create.output_tokens == 50
        assert span_create.duration_ms == 1000
        assert span_create.scope == "llm"
        assert span_create.type == "function"

    @pytest.mark.asyncio
    async def test_process_trace_success(self, processor, mock_settings):
        """Test successful trace processing."""
        project_uuid = uuid4()
        function_uuid = uuid4()
        user_id = uuid4()

        # Create trace buffer
        buffer = TraceBuffer("trace123")
        buffer.add_span(
            {
                "span_id": "parent",
                "parent_span_id": None,
                "user_id": str(user_id),
                "attributes": {
                    "lilypad.project.uuid": str(project_uuid),
                    "lilypad.function.uuid": str(function_uuid),
                },
            }
        )
        buffer.add_span(
            {
                "span_id": "child",
                "parent_span_id": "parent",
                "user_id": str(user_id),
                "attributes": {
                    "lilypad.project.uuid": str(project_uuid),
                    "lilypad.function.uuid": str(function_uuid),
                },
            }
        )
        processor.trace_buffers["trace123"] = buffer

        # Mock dependencies
        mock_session = AsyncMock()
        mock_user = MagicMock()
        mock_project = MagicMock()
        mock_project.organization_uuid = uuid4()

        with (
            patch(
                "lilypad.server.services.span_queue_processor.get_session"
            ) as mock_get_session,
            patch("lilypad.server.services.span_queue_processor.select"),
            patch(
                "lilypad.server.services.span_queue_processor.ProjectService"
            ) as mock_project_service,
            patch(
                "lilypad.server.services.span_queue_processor.SpanService"
            ) as mock_span_service,
            patch("lilypad.server.services.span_queue_processor.BillingService"),
        ):
            # Setup mocks
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            
            # Mock the exec result as an async operation
            mock_result = MagicMock()
            mock_result.first.return_value = mock_user
            mock_session.exec = AsyncMock(return_value=mock_result)

            mock_project_service.return_value.find_record_no_organization.return_value = mock_project
            mock_span_service.return_value.create_bulk_records = MagicMock()

            await processor._process_trace("trace123")

            # Verify trace was processed and removed from buffer
            assert "trace123" not in processor.trace_buffers
            mock_span_service.return_value.create_bulk_records.assert_called_once()


def test_get_span_queue_processor_singleton():
    """Test that get_span_queue_processor returns a singleton."""
    processor1 = get_span_queue_processor()
    processor2 = get_span_queue_processor()

    assert processor1 is processor2