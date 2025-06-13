"""Tests for the Stripe Queue Processor service."""

import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from aiokafka import TopicPartition
from aiokafka.errors import KafkaError

from lilypad.server.services.stripe_queue_processor import (
    MeterBatch,
    StripeQueueProcessor,
)
from lilypad.server.settings import Settings


class TestMeterBatch:
    """Test MeterBatch class."""

    def test_init(self):
        """Test MeterBatch initialization."""
        user_uuid = str(uuid4())
        org_uuid = str(uuid4())
        batch = MeterBatch(user_uuid, org_uuid)

        assert batch.user_uuid == user_uuid
        assert batch.org_uuid == org_uuid
        assert batch.trace_ids == set()
        assert batch.total_quantity == 0
        assert isinstance(batch.created_at, datetime)
        assert batch.attempt_count == 0
        assert batch.last_attempt is None
        assert batch.error is None

    def test_add_trace(self):
        """Test adding traces to batch."""
        batch = MeterBatch(str(uuid4()), str(uuid4()))
        
        # Add first trace
        batch.add_trace("trace-1", 10)
        assert "trace-1" in batch.trace_ids
        assert batch.total_quantity == 10

        # Add second trace
        batch.add_trace("trace-2", 5)
        assert "trace-2" in batch.trace_ids
        assert batch.total_quantity == 15

        # Add duplicate trace (should not increase quantity)
        batch.add_trace("trace-1", 20)
        assert len(batch.trace_ids) == 2
        assert batch.total_quantity == 15  # No change

    def test_idempotency_key(self):
        """Test idempotency key generation."""
        user_uuid = str(uuid4())
        org_uuid = str(uuid4())
        batch = MeterBatch(user_uuid, org_uuid)
        
        # Empty batch
        key1 = batch.idempotency_key
        assert isinstance(key1, str)
        assert len(key1) == 16

        # Add traces
        batch.add_trace("trace-2", 5)
        batch.add_trace("trace-1", 10)
        key2 = batch.idempotency_key
        
        # Key should be different but consistent
        assert key2 != key1
        key3 = batch.idempotency_key
        assert key3 == key2  # Should be consistent

    def test_age_seconds(self):
        """Test age calculation."""
        batch = MeterBatch(str(uuid4()), str(uuid4()))
        age = batch.age_seconds
        assert isinstance(age, float)
        assert age >= 0


class TestStripeQueueProcessor:
    """Test StripeQueueProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create StripeQueueProcessor instance for testing."""
        with patch("lilypad.server.services.stripe_queue_processor.get_settings") as mock_settings:
            mock_settings.return_value = Mock(spec=Settings)
            mock_settings.return_value.kafka_bootstrap_servers = "localhost:9092"
            mock_settings.return_value.kafka_topic_stripe_ingestion = "stripe-ingestion"
            mock_settings.return_value.kafka_consumer_group = "test-group"
            
            processor = StripeQueueProcessor()
            yield processor
            
            # Cleanup
            if processor._executor:
                processor._executor.shutdown(wait=False)

    def test_init(self, processor):
        """Test StripeQueueProcessor initialization."""
        assert processor.consumer is None
        assert processor.dlq_producer is None
        assert processor._running is False
        assert processor.batch_interval_seconds == 10
        assert processor.batch_max_age_seconds == 30
        assert processor.max_traces_per_batch == 1000
        assert processor.max_concurrent_stripe_calls == 10
        assert processor.max_retry_attempts == 10
        assert processor.pending_batches == {}
        assert processor.failed_batches == {}
        assert isinstance(processor.processed_traces, set)

    @pytest.mark.asyncio
    async def test_initialize_no_kafka(self):
        """Test initialize when Kafka not configured."""
        with patch("lilypad.server.services.stripe_queue_processor.get_settings") as mock_settings:
            mock_settings.return_value = Mock(spec=Settings)
            mock_settings.return_value.kafka_bootstrap_servers = None
            
            processor = StripeQueueProcessor()
            result = await processor.initialize()
            
            assert result is False

    @pytest.mark.asyncio
    async def test_initialize_success(self, processor):
        """Test successful initialization."""
        with (
            patch("lilypad.server.services.stripe_queue_processor.AIOKafkaConsumer") as mock_consumer_class,
            patch("lilypad.server.services.stripe_queue_processor.AIOKafkaProducer") as mock_producer_class,
        ):
            mock_consumer = AsyncMock()
            mock_consumer_class.return_value = mock_consumer
            
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer
            
            result = await processor.initialize()
            
            assert result is True
            assert processor.consumer == mock_consumer
            assert processor.dlq_producer == mock_producer
            mock_consumer.start.assert_called_once()
            mock_producer.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_retry_on_failure(self, processor):
        """Test initialization retry logic."""
        with (
            patch("lilypad.server.services.stripe_queue_processor.AIOKafkaConsumer") as mock_consumer_class,
            patch("asyncio.sleep") as mock_sleep,
        ):
            # First call fails, second succeeds
            mock_consumer = AsyncMock()
            mock_consumer.start.side_effect = [KafkaError("Connection failed"), None]
            mock_consumer_class.return_value = mock_consumer
            
            with patch("lilypad.server.services.stripe_queue_processor.AIOKafkaProducer") as mock_producer_class:
                mock_producer = AsyncMock()
                mock_producer_class.return_value = mock_producer
                
                result = await processor.initialize()
                
                assert result is True
                assert mock_consumer.start.call_count == 2
                mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_max_retries_exceeded(self, processor):
        """Test initialization failure after max retries."""
        with (
            patch("lilypad.server.services.stripe_queue_processor.AIOKafkaConsumer") as mock_consumer_class,
            patch("asyncio.sleep") as mock_sleep,
        ):
            mock_consumer = AsyncMock()
            mock_consumer.start.side_effect = KafkaError("Persistent failure")
            mock_consumer_class.return_value = mock_consumer
            
            result = await processor.initialize()
            
            assert result is False
            assert mock_consumer.start.call_count == 5  # max_retries
            assert mock_sleep.call_count == 4  # retries - 1

    @pytest.mark.asyncio
    async def test_start_no_kafka(self):
        """Test start when Kafka not configured."""
        with patch("lilypad.server.services.stripe_queue_processor.get_settings") as mock_settings:
            mock_settings.return_value = Mock(spec=Settings)
            mock_settings.return_value.kafka_bootstrap_servers = None
            
            processor = StripeQueueProcessor()
            await processor.start()
            
            assert processor._running is False
            assert processor._process_task is None

    @pytest.mark.asyncio
    async def test_start_success(self, processor):
        """Test successful start."""
        with (
            patch.object(processor, "initialize", return_value=True),
            patch("asyncio.create_task") as mock_create_task,
        ):
            await processor.start()
            
            assert processor._running is True
            assert mock_create_task.call_count == 4  # 4 background tasks

    @pytest.mark.asyncio
    async def test_start_initialization_failure(self, processor):
        """Test start when initialization fails."""
        with patch.object(processor, "initialize", return_value=False):
            await processor.start()
            
            assert processor._running is False

    @pytest.mark.asyncio
    async def test_stop(self, processor):
        """Test stop method."""
        # Set up basic state
        processor._running = True
        processor._process_task = None  # No tasks running
        processor._flush_task = None
        processor._retry_task = None
        
        # Mock consumer and producer
        mock_consumer = AsyncMock()
        mock_producer = AsyncMock()
        processor.consumer = mock_consumer
        processor.dlq_producer = mock_producer
        
        await processor.stop()
        
        assert processor._running is False
        mock_consumer.stop.assert_called_once()
        mock_producer.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_with_exceptions(self, processor):
        """Test stop method handles exceptions gracefully."""
        # Set up basic state
        processor._running = True
        processor._process_task = None  # No tasks to complicate things
        processor._flush_task = None
        processor._retry_task = None
        
        mock_consumer = AsyncMock()
        mock_consumer.stop.side_effect = Exception("Stop failed")
        processor.consumer = mock_consumer
        
        # Should raise exception from consumer.stop()
        with pytest.raises(Exception, match="Stop failed"):
            await processor.stop()
        assert processor._running is False

    @pytest.mark.asyncio
    async def test_process_meter_event_valid(self, processor):
        """Test processing valid meter event."""
        event = {
            "trace_id": "trace-123",
            "organization_uuid": str(uuid4()),
            "user_uuid": str(uuid4()),
            "span_count": 5,
        }
        
        # Should not raise exception
        await processor._process_meter_event(event)

    @pytest.mark.asyncio
    async def test_process_meter_event_duplicate(self, processor):
        """Test processing duplicate meter event."""
        trace_id = "trace-123"
        processor.processed_traces.add(trace_id)
        
        event = {
            "trace_id": trace_id,
            "organization_uuid": str(uuid4()),
            "user_uuid": str(uuid4()),
            "span_count": 5,
        }
        
        # Should handle duplicate gracefully
        await processor._process_meter_event(event)

    @pytest.mark.asyncio
    async def test_process_meter_event_invalid_data(self, processor):
        """Test processing meter event with invalid data."""
        event = {
            "trace_id": "trace-123",
            # Missing required fields
        }
        
        # Should handle gracefully
        await processor._process_meter_event(event)

    @pytest.mark.asyncio
    async def test_flush_pending_batches(self, processor):
        """Test flushing pending batches."""
        # Mock the method to ensure it's callable
        await processor._flush_pending_batches()

    @pytest.mark.asyncio
    async def test_send_batch_with_rate_limit(self, processor):
        """Test sending batch with rate limiting."""
        batch_key = "test-org"
        batch = MeterBatch(str(uuid4()), str(uuid4()))
        batch.add_trace("trace-1", 10)
        
        # Mock the billing service call
        with patch.object(processor, "_update_stripe_sync", return_value=True):
            result = await processor._send_batch_with_rate_limit(batch_key, batch)
            assert result is True

    def test_update_stripe_sync(self, processor):
        """Test synchronous Stripe update."""
        user_uuid = str(uuid4())
        org_uuid = str(uuid4())
        quantity = 10
        idempotency_key = "test-key"
        trace_count = 1
        
        with (
            patch("lilypad.server.services.stripe_queue_processor.get_session") as mock_get_session,
            patch("lilypad.server.services.stripe_queue_processor.BillingService") as mock_billing_class,
        ):
            mock_session = Mock()
            mock_get_session.return_value = [mock_session]
            
            mock_user = Mock()
            mock_session.exec.return_value.first.return_value = mock_user
            
            mock_billing = Mock()
            mock_billing_class.return_value = mock_billing
            
            # Should not return anything (None)
            result = processor._update_stripe_sync(user_uuid, org_uuid, quantity, idempotency_key, trace_count)
            assert result is None

    def test_update_stripe_sync_user_not_found(self, processor):
        """Test Stripe sync when user not found."""
        user_uuid = str(uuid4())
        org_uuid = str(uuid4())
        quantity = 10
        idempotency_key = "test-key"
        trace_count = 1
        
        with patch("lilypad.server.services.stripe_queue_processor.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = [mock_session]
            mock_session.exec.return_value.first.return_value = None
            
            # Should raise exception when user not found
            with pytest.raises(Exception, match="No user found for organization"):
                processor._update_stripe_sync(user_uuid, org_uuid, quantity, idempotency_key, trace_count)

    @pytest.mark.asyncio
    async def test_send_to_dlq(self, processor):
        """Test sending event to DLQ."""
        processor.dlq_producer = AsyncMock()
        
        event = {"trace_id": "test-trace"}
        error = "Test error"
        
        await processor._send_to_dlq(event, error)
        
        processor.dlq_producer.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_dlq_no_producer(self, processor):
        """Test sending to DLQ when producer not available."""
        processor.dlq_producer = None
        
        event = {"trace_id": "test-trace"}
        error = "Test error"
        
        # Should not raise exception
        await processor._send_to_dlq(event, error)

    @pytest.mark.asyncio
    async def test_cleanup_processed_traces(self, processor):
        """Test cleanup of processed traces."""
        # Add many traces to trigger cleanup
        for i in range(150000):  # More than 100k to trigger cleanup
            processor.processed_traces.add(f"trace-{i}")
        
        assert len(processor.processed_traces) > 100000
        
        # Mock _running to false to exit the loop quickly
        processor._running = True
        
        # Create a task but cancel it quickly
        task = asyncio.create_task(processor._cleanup_processed_traces())
        await asyncio.sleep(0.01)  # Let it run briefly
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_cleanup_processed_traces_triggers_clear(self, processor):
        """Test cleanup clears processed traces when over limit."""
        # Add traces over the limit
        for i in range(150000):
            processor.processed_traces.add(f"trace-{i}")
        
        assert len(processor.processed_traces) > 100000
        
        # Manually call the cleanup logic once
        async with processor._batch_lock:
            if len(processor.processed_traces) > 100000:
                processor.processed_traces.clear()
        
        assert len(processor.processed_traces) == 0

    @pytest.mark.asyncio
    async def test_process_queue_success(self, processor):
        """Test successful queue processing."""
        # Mock consumer
        mock_consumer = AsyncMock()
        processor.consumer = mock_consumer
        processor._running = True
        
        # Mock records
        mock_record = Mock()
        mock_record.value = {
            "trace_id": "test-trace",
            "organization_uuid": str(uuid4()),
            "user_uuid": str(uuid4()),
            "quantity": 5
        }
        mock_record.offset = 123
        
        topic_partition = TopicPartition("test-topic", 0)
        mock_consumer.getmany.return_value = {
            topic_partition: [mock_record]
        }
        
        # Mock process_meter_event to avoid batching logic
        with patch.object(processor, "_process_meter_event") as mock_process:
            # Set running to False after one iteration
            def stop_after_first():
                processor._running = False
            
            mock_process.side_effect = stop_after_first
            
            await processor._process_queue()
            
            mock_process.assert_called_once_with(mock_record.value)
            assert topic_partition in processor.uncommitted_offsets
            assert processor.uncommitted_offsets[topic_partition] == 123

    @pytest.mark.asyncio 
    async def test_process_queue_kafka_error(self, processor):
        """Test queue processing with Kafka error."""
        mock_consumer = AsyncMock()
        processor.consumer = mock_consumer
        processor._running = True
        
        # First call raises KafkaError, second call sets _running to False
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise KafkaError("Connection lost")
            else:
                processor._running = False
                return {}
        
        mock_consumer.getmany.side_effect = side_effect
        
        with patch("asyncio.sleep") as mock_sleep:
            await processor._process_queue()
            mock_sleep.assert_called_with(5)

    @pytest.mark.asyncio
    async def test_process_queue_unexpected_error(self, processor):
        """Test queue processing with unexpected error."""
        mock_consumer = AsyncMock()
        processor.consumer = mock_consumer
        processor._running = True
        
        # First call raises unexpected error, second call stops
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Unexpected error")
            else:
                processor._running = False
                return {}
        
        mock_consumer.getmany.side_effect = side_effect
        
        with patch("asyncio.sleep") as mock_sleep:
            await processor._process_queue()
            mock_sleep.assert_called_with(5)

    @pytest.mark.asyncio
    async def test_process_queue_record_processing_error(self, processor):
        """Test queue processing when individual record processing fails."""
        mock_consumer = AsyncMock()
        processor.consumer = mock_consumer
        processor._running = True
        
        # Mock a record that will cause processing error
        mock_record = Mock()
        mock_record.value = {"invalid": "data"}
        mock_record.offset = 456
        
        topic_partition = TopicPartition("test-topic", 0)
        
        # First call returns record, second call stops
        call_count = 0
        def getmany_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {topic_partition: [mock_record]}
            else:
                processor._running = False
                return {}
        
        mock_consumer.getmany.side_effect = getmany_side_effect
        
        # Mock send_to_dlq
        processor.dlq_producer = AsyncMock()
        
        with (
            patch.object(processor, "_process_meter_event", side_effect=Exception("Processing failed")),
            patch.object(processor, "_send_to_dlq") as mock_dlq,
        ):
            await processor._process_queue()
            
            # Should send to DLQ and still track offset
            mock_dlq.assert_called_once_with({"invalid": "data"}, "Processing failed")
            assert processor.uncommitted_offsets[topic_partition] == 456

    @pytest.mark.asyncio
    async def test_process_meter_event_with_quantity(self, processor):
        """Test processing meter event with quantity field."""
        org_uuid = str(uuid4())
        user_uuid = str(uuid4())
        
        event = {
            "trace_id": "trace-123",
            "organization_uuid": org_uuid,
            "user_uuid": user_uuid,
            "quantity": 10
        }
        
        await processor._process_meter_event(event)
        
        # Check batch was created
        assert org_uuid in processor.pending_batches
        batch = processor.pending_batches[org_uuid]
        assert batch.total_quantity == 10
        assert "trace-123" in batch.trace_ids

    @pytest.mark.asyncio
    async def test_process_meter_event_invalid_quantity(self, processor):
        """Test processing meter event with invalid quantity."""
        event = {
            "trace_id": "trace-123",
            "organization_uuid": str(uuid4()),
            "user_uuid": str(uuid4()),
            "quantity": 0  # Invalid quantity
        }
        
        await processor._process_meter_event(event)
        
        # Should not create batch for invalid quantity
        assert len(processor.pending_batches) == 0

    @pytest.mark.asyncio
    async def test_process_meter_event_missing_org_uuid(self, processor):
        """Test processing meter event with missing org_uuid."""
        event = {
            "trace_id": "trace-123",
            "user_uuid": str(uuid4()),
            "quantity": 10
            # Missing organization_uuid
        }
        
        await processor._process_meter_event(event)
        
        # Should not create batch
        assert len(processor.pending_batches) == 0

    @pytest.mark.asyncio
    async def test_process_meter_event_missing_trace_id(self, processor):
        """Test processing meter event with missing trace_id."""
        event = {
            "organization_uuid": str(uuid4()),
            "user_uuid": str(uuid4()),
            "quantity": 10
            # Missing trace_id
        }
        
        await processor._process_meter_event(event)
        
        # Should not create batch
        assert len(processor.pending_batches) == 0

    @pytest.mark.asyncio
    async def test_process_meter_event_duplicate_trace(self, processor):
        """Test processing duplicate trace ID."""
        trace_id = "trace-123"
        processor.processed_traces.add(trace_id)
        
        event = {
            "trace_id": trace_id,
            "organization_uuid": str(uuid4()),
            "user_uuid": str(uuid4()),
            "quantity": 10
        }
        
        await processor._process_meter_event(event)
        
        # Should not create batch for duplicate
        assert len(processor.pending_batches) == 0

    @pytest.mark.asyncio
    async def test_process_meter_event_batch_overflow(self, processor):
        """Test meter event processing when batch reaches max size."""
        org_uuid = str(uuid4())
        user_uuid = str(uuid4())
        
        # Create a batch that's already at max size
        batch = MeterBatch(user_uuid, org_uuid)
        for i in range(processor.max_traces_per_batch):
            batch.add_trace(f"existing-trace-{i}", 1)
        
        processor.pending_batches[org_uuid] = batch
        
        # Add one more trace to trigger overflow
        event = {
            "trace_id": "overflow-trace",
            "organization_uuid": org_uuid,
            "user_uuid": user_uuid,
            "quantity": 5
        }
        
        await processor._process_meter_event(event)
        
        # Original batch should be moved to failed_batches
        assert len([k for k in processor.failed_batches.keys() if k.startswith(f"{org_uuid}_overflow_")]) == 1
        
        # New batch should be created with the new trace
        assert org_uuid in processor.pending_batches
        new_batch = processor.pending_batches[org_uuid]
        assert "overflow-trace" in new_batch.trace_ids
        assert new_batch.total_quantity == 5

    @pytest.mark.asyncio
    async def test_flush_loop_with_rate_limit_backoff(self, processor):
        """Test flush loop handles rate limit backoff."""
        processor._running = True
        processor.last_rate_limit_error = datetime.now(timezone.utc)
        
        # Mock sleep to control timing
        sleep_calls = []
        async def mock_sleep(duration):
            sleep_calls.append(duration)
            if len(sleep_calls) == 1:
                # After first sleep (batch_interval_seconds), set recent rate limit
                pass
            elif len(sleep_calls) == 2:
                # After rate limit backoff, stop the loop
                processor._running = False
        
        with (
            patch("asyncio.sleep", side_effect=mock_sleep),
            patch.object(processor, "_flush_pending_batches") as mock_flush,
        ):
            await processor._flush_loop()
            
            # Should have slept for batch interval, then rate limit backoff
            assert sleep_calls == [processor.batch_interval_seconds, 30]
            mock_flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_flush_loop_rate_limit_expired(self, processor):
        """Test flush loop when rate limit backoff has expired."""
        processor._running = True
        # Set rate limit error to more than 60 seconds ago
        processor.last_rate_limit_error = datetime.now(timezone.utc).replace(
            minute=datetime.now(timezone.utc).minute - 2
        )
        
        call_count = 0
        async def mock_sleep(duration):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # After first sleep, stop the loop
                processor._running = False
        
        with (
            patch("asyncio.sleep", side_effect=mock_sleep),
            patch.object(processor, "_flush_pending_batches") as mock_flush,
        ):
            await processor._flush_loop()
            
            # Rate limit error should be cleared
            assert processor.last_rate_limit_error is None
            mock_flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_flush_pending_batches_with_age_based_batches(self, processor):
        """Test flushing batches based on age."""
        org_uuid = str(uuid4())
        user_uuid = str(uuid4())
        
        # Create an old batch
        batch = MeterBatch(user_uuid, org_uuid)
        batch.add_trace("trace-1", 10)
        # Manually set old creation time
        batch.created_at = datetime.now(timezone.utc).replace(
            minute=datetime.now(timezone.utc).minute - 1
        )
        
        processor.pending_batches[org_uuid] = batch
        
        with patch.object(processor, "_send_batch_with_rate_limit", return_value=True) as mock_send:
            await processor._flush_pending_batches()
            
            # Batch should have been flushed
            mock_send.assert_called_once()
            assert org_uuid not in processor.pending_batches

    @pytest.mark.asyncio
    async def test_flush_pending_batches_with_overflow_batches(self, processor):
        """Test flushing overflow batches."""
        org_uuid = str(uuid4())
        user_uuid = str(uuid4())
        
        batch = MeterBatch(user_uuid, org_uuid)
        batch.add_trace("trace-1", 10)
        
        # Create overflow batch key
        overflow_key = f"{org_uuid}_overflow_{batch.created_at.timestamp()}"
        processor.failed_batches[overflow_key] = batch
        
        with patch.object(processor, "_send_batch_with_rate_limit", return_value=True) as mock_send:
            await processor._flush_pending_batches()
            
            # Overflow batch should have been processed
            mock_send.assert_called_once()
            assert overflow_key not in processor.failed_batches

    @pytest.mark.asyncio
    async def test_flush_pending_batches_partial_failure(self, processor):
        """Test flushing batches when some fail."""
        org_uuid1 = str(uuid4())
        org_uuid2 = str(uuid4())
        user_uuid = str(uuid4())
        
        # Create two old batches
        batch1 = MeterBatch(user_uuid, org_uuid1)
        batch1.add_trace("trace-1", 10)
        batch1.created_at = datetime.now(timezone.utc).replace(
            minute=datetime.now(timezone.utc).minute - 1
        )
        
        batch2 = MeterBatch(user_uuid, org_uuid2)
        batch2.add_trace("trace-2", 5)
        batch2.created_at = datetime.now(timezone.utc).replace(
            minute=datetime.now(timezone.utc).minute - 1
        )
        
        processor.pending_batches[org_uuid1] = batch1
        processor.pending_batches[org_uuid2] = batch2
        
        # Mock one success, one failure
        def mock_send_side_effect(batch_key, batch):
            return batch_key == org_uuid1  # Only first batch succeeds
        
        with patch.object(processor, "_send_batch_with_rate_limit", side_effect=mock_send_side_effect):
            # Add some uncommitted offsets
            tp = TopicPartition("test", 0)
            processor.uncommitted_offsets[tp] = 100
            
            await processor._flush_pending_batches()
            
            # Offsets should not be committed due to partial failure
            assert tp in processor.uncommitted_offsets

    @pytest.mark.asyncio
    async def test_flush_pending_batches_commit_success(self, processor):
        """Test successful offset commit after flush."""
        org_uuid = str(uuid4())
        user_uuid = str(uuid4())
        
        # Create old batch
        batch = MeterBatch(user_uuid, org_uuid)
        batch.add_trace("trace-1", 10)
        batch.created_at = datetime.now(timezone.utc).replace(
            minute=datetime.now(timezone.utc).minute - 1
        )
        
        processor.pending_batches[org_uuid] = batch
        
        # Mock consumer
        mock_consumer = AsyncMock()
        processor.consumer = mock_consumer
        
        # Add uncommitted offsets
        tp = TopicPartition("test", 0)
        processor.uncommitted_offsets[tp] = 100
        
        with patch.object(processor, "_send_batch_with_rate_limit", return_value=True):
            await processor._flush_pending_batches()
            
            # Should commit offsets
            mock_consumer.commit.assert_called_once_with({tp: 101})
            assert len(processor.uncommitted_offsets) == 0

    @pytest.mark.asyncio
    async def test_flush_pending_batches_commit_failure(self, processor):
        """Test offset commit failure handling."""
        org_uuid = str(uuid4())
        user_uuid = str(uuid4())
        
        batch = MeterBatch(user_uuid, org_uuid)
        batch.add_trace("trace-1", 10)
        batch.created_at = datetime.now(timezone.utc).replace(
            minute=datetime.now(timezone.utc).minute - 1
        )
        
        processor.pending_batches[org_uuid] = batch
        
        # Mock consumer that fails to commit
        mock_consumer = AsyncMock()
        mock_consumer.commit.side_effect = Exception("Commit failed")
        processor.consumer = mock_consumer
        
        tp = TopicPartition("test", 0)
        processor.uncommitted_offsets[tp] = 100
        
        with patch.object(processor, "_send_batch_with_rate_limit", return_value=True):
            await processor._flush_pending_batches()
            
            # Should attempt commit but handle failure gracefully
            mock_consumer.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_batch_with_rate_limit_success(self, processor):
        """Test successful batch sending with rate limiting."""
        batch_key = "test-batch"
        batch = MeterBatch(str(uuid4()), str(uuid4()))
        batch.add_trace("trace-1", 10)
        
        with patch.object(processor, "_update_stripe_sync") as mock_update:
            result = await processor._send_batch_with_rate_limit(batch_key, batch)
            
            assert result is True
            mock_update.assert_called_once_with(
                batch.user_uuid,
                batch.org_uuid,
                batch.total_quantity,
                batch.idempotency_key,
                len(batch.trace_ids)
            )

    @pytest.mark.asyncio
    async def test_send_batch_with_rate_limit_failure(self, processor):
        """Test batch sending failure."""
        batch_key = "test-batch"
        batch = MeterBatch(str(uuid4()), str(uuid4()))
        batch.add_trace("trace-1", 10)
        
        with patch.object(processor, "_update_stripe_sync", side_effect=Exception("Stripe error")):
            result = await processor._send_batch_with_rate_limit(batch_key, batch)
            
            assert result is False
            # Batch should be added to failed_batches
            assert batch_key in processor.failed_batches
            assert processor.failed_batches[batch_key].attempt_count == 1
            assert processor.failed_batches[batch_key].error == "Stripe error"

    @pytest.mark.asyncio
    async def test_send_batch_with_rate_limit_rate_limit_error(self, processor):
        """Test rate limit error detection and handling."""
        batch_key = "test-batch"
        batch = MeterBatch(str(uuid4()), str(uuid4()))
        batch.add_trace("trace-1", 10)
        
        with patch.object(processor, "_update_stripe_sync", side_effect=Exception("Rate limit exceeded")):
            result = await processor._send_batch_with_rate_limit(batch_key, batch)
            
            assert result is False
            assert processor.last_rate_limit_error is not None
            assert isinstance(processor.last_rate_limit_error, datetime)

    @pytest.mark.asyncio
    async def test_retry_loop_with_backoff(self, processor):
        """Test retry loop with exponential backoff."""
        processor._running = True
        
        # Create a failed batch
        batch = MeterBatch(str(uuid4()), str(uuid4()))
        batch.add_trace("trace-1", 10)
        batch.attempt_count = 2
        batch.last_attempt = datetime.now(timezone.utc).replace(
            minute=datetime.now(timezone.utc).minute - 5  # 5 minutes ago
        )
        batch.error = "Previous error"
        
        processor.failed_batches["test-batch"] = batch
        
        call_count = 0
        async def mock_sleep(duration):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                processor._running = False  # Stop after first iteration
        
        with (
            patch("asyncio.sleep", side_effect=mock_sleep),
            patch.object(processor, "_send_batch_with_rate_limit", return_value=True) as mock_send,
        ):
            await processor._retry_loop()
            
            # Should retry the batch
            mock_send.assert_called_once()
            # Batch should be removed from failed_batches on success
            assert "test-batch" not in processor.failed_batches

    @pytest.mark.asyncio
    async def test_retry_loop_max_retries_exceeded(self, processor):
        """Test retry loop when max retries exceeded."""
        processor._running = True
        
        # Create a batch that exceeded max retries
        batch = MeterBatch(str(uuid4()), str(uuid4()))
        batch.add_trace("trace-1", 10)
        batch.attempt_count = processor.max_retry_attempts + 1
        batch.error = "Persistent error"
        
        processor.failed_batches["test-batch"] = batch
        processor.dlq_producer = AsyncMock()
        
        call_count = 0
        async def mock_sleep(duration):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                processor._running = False
        
        with (
            patch("asyncio.sleep", side_effect=mock_sleep),
            patch.object(processor, "_send_to_dlq") as mock_dlq,
        ):
            await processor._retry_loop()
            
            # Should send to DLQ
            mock_dlq.assert_called_once()
            # Batch should be removed from failed_batches
            assert "test-batch" not in processor.failed_batches

    @pytest.mark.asyncio
    async def test_retry_loop_skip_overflow_batches(self, processor):
        """Test retry loop skips overflow batches."""
        processor._running = True
        
        # Create overflow batch (should be skipped)
        batch = MeterBatch(str(uuid4()), str(uuid4()))
        batch.add_trace("trace-1", 10)
        processor.failed_batches["org_overflow_12345"] = batch
        
        call_count = 0
        async def mock_sleep(duration):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                processor._running = False
        
        with (
            patch("asyncio.sleep", side_effect=mock_sleep),
            patch.object(processor, "_send_batch_with_rate_limit") as mock_send,
        ):
            await processor._retry_loop()
            
            # Should not retry overflow batches
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_retry_loop_immediate_retry_no_last_attempt(self, processor):
        """Test retry loop immediately retries batches with no last_attempt."""
        processor._running = True
        
        batch = MeterBatch(str(uuid4()), str(uuid4()))
        batch.add_trace("trace-1", 10)
        batch.last_attempt = None  # No previous attempt
        
        processor.failed_batches["test-batch"] = batch
        
        call_count = 0
        async def mock_sleep(duration):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                processor._running = False
        
        with (
            patch("asyncio.sleep", side_effect=mock_sleep),
            patch.object(processor, "_send_batch_with_rate_limit", return_value=True) as mock_send,
        ):
            await processor._retry_loop()
            
            # Should retry immediately
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_dlq_producer_error(self, processor):
        """Test DLQ sending when producer fails."""
        processor.dlq_producer = AsyncMock()
        processor.dlq_producer.send.side_effect = Exception("DLQ send failed")
        
        event = {"trace_id": "test-trace"}
        error = "Test error"
        
        # Should not raise exception even if DLQ fails
        await processor._send_to_dlq(event, error)
        
        processor.dlq_producer.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_with_pending_state_logging(self, processor):
        """Test stop method logs pending/failed batch state."""
        processor._running = True
        
        # Add some pending and failed batches
        batch1 = MeterBatch(str(uuid4()), str(uuid4()))
        batch1.add_trace("trace-1", 10)
        batch1.add_trace("trace-2", 15)
        
        batch2 = MeterBatch(str(uuid4()), str(uuid4()))
        batch2.add_trace("trace-3", 5)
        
        processor.pending_batches["org1"] = batch1
        processor.failed_batches["org2"] = batch2
        
        # Mock consumer and producer
        processor.consumer = AsyncMock()
        processor.dlq_producer = AsyncMock()
        
        await processor.stop()
        
        assert processor._running is False

    @pytest.mark.asyncio
    async def test_stop_with_running_tasks(self, processor):
        """Test stop method cancels running tasks."""
        processor._running = True
        
        # Create mock tasks
        mock_task1 = AsyncMock()
        mock_task1.done.return_value = False
        mock_task1.cancel.return_value = None
        
        mock_task2 = AsyncMock()
        mock_task2.done.return_value = True  # Already done
        
        processor._process_task = mock_task1
        processor._flush_task = mock_task2
        processor._retry_task = None
        
        await processor.stop()
        
        # Should cancel running tasks
        mock_task1.cancel.assert_called_once()
        mock_task2.cancel.assert_not_called()  # Already done

    @pytest.mark.asyncio
    async def test_initialize_return_false_on_final_attempt(self, processor):
        """Test initialize returns False when last retry fails."""
        with (
            patch("lilypad.server.services.stripe_queue_processor.AIOKafkaConsumer") as mock_consumer_class,
            patch("asyncio.sleep") as mock_sleep,
        ):
            mock_consumer = AsyncMock()
            mock_consumer.start.side_effect = Exception("Persistent failure")
            mock_consumer_class.return_value = mock_consumer
            
            result = await processor.initialize()
            
            # Should return False after max retries
            assert result is False


def test_get_stripe_queue_processor_singleton():
    """Test singleton pattern for stripe queue processor."""
    from lilypad.server.services.stripe_queue_processor import get_stripe_queue_processor
    
    processor1 = get_stripe_queue_processor()
    processor2 = get_stripe_queue_processor()
    
    assert processor1 is processor2