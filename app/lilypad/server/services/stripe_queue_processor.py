"""Stripe Queue Processor service for consuming span meter events from Kafka."""

import asyncio
import contextlib
import hashlib
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer, TopicPartition
from aiokafka.errors import KafkaError
from sqlmodel import select

from ..db.session import get_session
from ..models.users import UserTable
from ..settings import get_settings
from .billing import BillingService

logger = logging.getLogger(__name__)


class MeterBatch:
    """Represents a batch of meter updates for an organization."""

    def __init__(self, user_uuid: str, org_uuid: str) -> None:
        self.user_uuid = user_uuid
        self.org_uuid = org_uuid
        self.trace_ids: set[str] = set()
        self.total_quantity = 0
        self.created_at = datetime.now(timezone.utc)
        self.attempt_count = 0
        self.last_attempt: datetime | None = None
        self.error: str | None = None

    def add_trace(self, trace_id: str, quantity: int) -> None:
        """Add a trace to this batch."""
        if trace_id not in self.trace_ids:
            self.trace_ids.add(trace_id)
            self.total_quantity += quantity

    @property
    def idempotency_key(self) -> str:
        """Generate idempotency key for this batch."""
        # Sort trace IDs for consistent key generation
        sorted_traces = sorted(self.trace_ids)
        # Include timestamp to allow rebatching if needed
        timestamp = self.created_at.strftime("%Y%m%d%H%M%S")
        raw = f"{self.org_uuid}:{timestamp}:{','.join(sorted_traces[:10])}"  # First 10 traces
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @property
    def age_seconds(self) -> float:
        """Get age of this batch in seconds."""
        return (datetime.now(timezone.utc) - self.created_at).total_seconds()


class StripeQueueProcessor:
    """Service for processing span meter events with:
    - Intelligent batching to respect Stripe rate limits
    - At-least-once delivery guarantees
    - Automatic retries with exponential backoff
    - Dead letter queue for failed events
    - Duplicate detection within batching windows
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.consumer: AIOKafkaConsumer | None = None
        self.dlq_producer: AIOKafkaProducer | None = None
        self._running = False

        # Configuration
        self.batch_interval_seconds = 10  # How often to flush batches
        self.batch_max_age_seconds = 30  # Max age before force flush
        self.max_traces_per_batch = 1000  # Max traces to include in one batch
        self.max_concurrent_stripe_calls = 10  # Rate limit protection
        self.max_retry_attempts = 10

        # Tasks
        self._process_task: asyncio.Task | None = None
        self._flush_task: asyncio.Task | None = None
        self._retry_task: asyncio.Task | None = None

        # Batching state
        self.pending_batches: dict[str, MeterBatch] = {}  # org_uuid -> MeterBatch
        self.failed_batches: dict[str, MeterBatch] = {}  # org_uuid -> MeterBatch
        self.processed_traces: set[str] = set()  # Recently processed trace IDs
        self._batch_lock = asyncio.Lock()

        # Rate limiting
        self.rate_limiter = asyncio.Semaphore(self.max_concurrent_stripe_calls)
        self.last_rate_limit_error: datetime | None = None

        # Uncommitted offsets for at-least-once delivery
        self.uncommitted_offsets: dict[TopicPartition, int] = {}

        # Thread pool for Stripe operations
        self._executor = ThreadPoolExecutor(
            max_workers=3,
            thread_name_prefix="stripe-worker",
        )

        logger.info(
            f"Initialized StripeQueueProcessor - "
            f"Batch interval: {self.batch_interval_seconds}s, "
            f"Max concurrent calls: {self.max_concurrent_stripe_calls}"
        )

    async def initialize(self) -> bool:
        """Initialize Kafka consumer and DLQ producer."""
        if not self.settings.kafka_bootstrap_servers:
            logger.warning("Kafka not configured, stripe meter processor disabled")
            return False

        # Retry logic for initialization
        max_retries = 5
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # Consumer with manual commit for at-least-once delivery
                self.consumer = AIOKafkaConsumer(
                    self.settings.kafka_topic_stripe_ingestion,
                    bootstrap_servers=self.settings.kafka_bootstrap_servers,
                    group_id=f"{self.settings.kafka_consumer_group}-stripe",
                    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                    enable_auto_commit=False,  # Manual commit for reliability
                    auto_offset_reset="earliest",
                    session_timeout_ms=30000,
                    heartbeat_interval_ms=10000,
                    max_poll_records=500,  # Process more records at once
                )
                await self.consumer.start()

                # DLQ producer for failed events
                self.dlq_producer = AIOKafkaProducer(
                    bootstrap_servers=self.settings.kafka_bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    compression_type="gzip",  # Compress DLQ messages
                )
                await self.dlq_producer.start()

                logger.info(
                    f"✅ Stripe meter processor initialized - "
                    f"Topic: {self.settings.kafka_topic_stripe_ingestion}"
                )
                return True

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Kafka initialization attempt {attempt + 1}/{max_retries} failed, "
                        f"retrying in {retry_delay}s: {e}"
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(
                        f"Failed to initialize Kafka after {max_retries} attempts: {e}"
                    )
                    return False

        return False

    async def start(self) -> None:
        """Start the processor with all background tasks."""
        if not await self.initialize():
            return

        self._running = True

        # Start background tasks
        self._process_task = asyncio.create_task(self._process_queue())
        self._flush_task = asyncio.create_task(self._flush_loop())
        self._retry_task = asyncio.create_task(self._retry_loop())

        # Cleanup old processed traces periodically
        asyncio.create_task(self._cleanup_processed_traces())

        logger.info("🚀 StripeQueueProcessor started with all tasks")

    async def stop(self) -> None:
        """Graceful shutdown with state logging."""
        logger.info("Stopping StripeQueueProcessor...")
        self._running = False

        # Log what we're losing
        async with self._batch_lock:
            total_pending = sum(b.total_quantity for b in self.pending_batches.values())
            total_failed = sum(b.total_quantity for b in self.failed_batches.values())

            if total_pending > 0 or total_failed > 0:
                logger.warning(
                    f"⚠️  SHUTTING DOWN WITH UNBILLED SPANS: "
                    f"Pending: {total_pending} spans across {len(self.pending_batches)} orgs, "
                    f"Failed: {total_failed} spans across {len(self.failed_batches)} orgs. "
                    f"These will be reprocessed on restart from Kafka."
                )

        # Cancel all tasks
        tasks = [self._process_task, self._flush_task, self._retry_task]
        for task in tasks:
            if task and not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

        # Stop Kafka connections
        if self.consumer:
            await self.consumer.stop()
        if self.dlq_producer:
            await self.dlq_producer.stop()

        # Shutdown thread pool
        self._executor.shutdown(wait=True, cancel_futures=False)

        logger.info("✅ StripeQueueProcessor stopped")

    async def _process_queue(self) -> None:
        """Main queue processing loop with batch commit."""
        logger.info("Starting meter event processing loop...")

        while self._running:
            try:
                records = await self.consumer.getmany(timeout_ms=1000, max_records=500)  # pyright: ignore [reportOptionalMemberAccess]

                if not records:
                    continue

                msg_count = sum(len(msgs) for msgs in records.values())
                logger.debug(f"Processing {msg_count} meter events")

                # Process all messages and track offsets
                batch_offsets = {}
                for topic_partition, messages in records.items():
                    for record in messages:
                        try:
                            await self._process_meter_event(record.value)
                            # Track highest offset per partition
                            batch_offsets[topic_partition] = record.offset
                        except Exception as e:
                            logger.error(
                                f"Failed to process meter event: {e}", exc_info=True
                            )
                            # Send to DLQ but continue processing
                            await self._send_to_dlq(record.value, str(e))
                            # Still track offset to avoid reprocessing bad messages
                            batch_offsets[topic_partition] = record.offset

                # Store offsets for commit after successful flush
                async with self._batch_lock:
                    self.uncommitted_offsets.update(batch_offsets)

            except KafkaError as e:
                logger.error(f"Kafka error in processing loop: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error in processing loop: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def _process_meter_event(self, event: Any) -> None:
        """Add meter event to appropriate batch with deduplication."""
        user_uuid = event.get("user_uuid")
        org_uuid = event.get("organization_uuid")
        quantity = event.get("quantity", 0)
        trace_id = event.get("trace_id")

        if not org_uuid or quantity <= 0 or not trace_id:
            logger.warning(f"Invalid meter event: {event}")
            return

        async with self._batch_lock:
            # Check if we've recently processed this trace
            if trace_id in self.processed_traces:
                logger.debug(f"Skipping duplicate trace: {trace_id}")
                return

            # Add to processed set (will be cleaned up periodically)
            self.processed_traces.add(trace_id)

            # Get or create batch for this org
            if org_uuid not in self.pending_batches:
                self.pending_batches[org_uuid] = MeterBatch(user_uuid, org_uuid)

            batch = self.pending_batches[org_uuid]

            # Check if batch is getting too large
            if len(batch.trace_ids) >= self.max_traces_per_batch:
                logger.info(
                    f"Batch for {org_uuid} reached max size ({self.max_traces_per_batch} traces), "
                    f"creating new batch"
                )
                # Move current batch to a temporary location for immediate flush
                self.failed_batches[
                    f"{org_uuid}_overflow_{datetime.now(timezone.utc)}"
                ] = batch
                # Create new batch
                self.pending_batches[org_uuid] = MeterBatch(user_uuid, org_uuid)
                batch = self.pending_batches[org_uuid]

            # Add trace to batch
            batch.add_trace(trace_id, quantity)
            logger.debug(
                f"Added to batch - Org: {org_uuid}, Trace: {trace_id}, "
                f"Quantity: {quantity}, Batch total: {batch.total_quantity}"
            )

    async def _flush_loop(self) -> None:
        """Periodically flush batches to Stripe."""
        while self._running:
            await asyncio.sleep(self.batch_interval_seconds)

            # Check for rate limit backoff
            if self.last_rate_limit_error:
                time_since_error = (
                    datetime.now(timezone.utc) - self.last_rate_limit_error
                ).total_seconds()
                if time_since_error < 60:
                    logger.warning("Recent rate limit error, backing off for 30s")
                    await asyncio.sleep(30)
                else:
                    self.last_rate_limit_error = None

            await self._flush_pending_batches()

    async def _flush_pending_batches(self) -> None:
        """Flush ready batches to Stripe and commit Kafka offsets."""
        async with self._batch_lock:
            # Find batches ready to send
            ready_batches = {}
            for org_uuid, batch in list(self.pending_batches.items()):
                if batch.age_seconds >= self.batch_interval_seconds:
                    ready_batches[org_uuid] = self.pending_batches.pop(org_uuid)

            # Also check for any overflow batches
            for key, batch in list(self.failed_batches.items()):
                if key.endswith(f"_overflow_{batch.created_at.timestamp()}"):
                    ready_batches[key] = self.failed_batches.pop(key)

        if not ready_batches:
            return

        logger.info(f"📤 Flushing {len(ready_batches)} batches to Stripe")

        # Process batches with rate limiting
        tasks = []
        for org_uuid, batch in ready_batches.items():
            task = asyncio.create_task(
                self._send_batch_with_rate_limit(org_uuid, batch)
            )
            tasks.append(task)

        # Wait for all sends to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check results and handle failures
        all_successful = True
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Failed to send batch: {result}")
                all_successful = False
            elif result is False:
                all_successful = False

        # Commit Kafka offsets only if all batches were successful
        if all_successful and self.uncommitted_offsets:
            try:
                async with self._batch_lock:
                    if self.consumer:
                        for tp, offset in self.uncommitted_offsets.items():
                            await self.consumer.commit({tp: offset + 1})
                        self.uncommitted_offsets.clear()
                        logger.debug("Committed Kafka offsets after successful flush")
            except Exception as e:
                logger.error(f"Failed to commit offsets: {e}")

    async def _send_batch_with_rate_limit(
        self, batch_key: str, batch: MeterBatch
    ) -> bool:
        """Send batch to Stripe with rate limiting."""
        async with self.rate_limiter:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    self._executor,
                    self._update_stripe_sync,
                    batch.user_uuid,
                    batch.org_uuid,
                    batch.total_quantity,
                    batch.idempotency_key,
                    len(batch.trace_ids),
                )

                logger.info(
                    f"✅ Sent batch - Org: {batch.org_uuid}, "
                    f"Spans: {batch.total_quantity}, Traces: {len(batch.trace_ids)}"
                )
                return True

            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to send batch for {batch.org_uuid}: {error_msg}")

                # Check if it's a rate limit error
                if "rate" in error_msg.lower() and "limit" in error_msg.lower():
                    self.last_rate_limit_error = datetime.now(timezone.utc)

                # Add to failed batches for retry
                async with self._batch_lock:
                    batch.attempt_count += 1
                    batch.last_attempt = datetime.now(timezone.utc)
                    batch.error = error_msg
                    self.failed_batches[batch_key] = batch

                return False

    def _update_stripe_sync(
        self,
        user_uuid: str,
        org_uuid: str,
        quantity: int,
        idempotency_key: str,
        trace_count: int,
    ) -> None:
        """Synchronous Stripe update in thread pool."""
        for session in get_session():
            # Get any user from the organization for billing context
            result = session.exec(
                select(UserTable).where(UserTable.uuid == UUID(user_uuid)).limit(1)
            )
            user = result.first()

            if not user:
                raise Exception(f"No user found for organization {org_uuid}")

            billing_service = BillingService(session, user)  # pyright: ignore [reportArgumentType]

            # Call billing service
            billing_service.report_span_usage(UUID(org_uuid), quantity=quantity)

            logger.info(
                f"Stripe meter updated - Org: {org_uuid}, Spans: {quantity}, "
                f"Traces: {trace_count}, Idempotency: {idempotency_key}"
            )

    async def _retry_loop(self) -> None:
        """Retry failed batches with exponential backoff."""
        while self._running:
            await asyncio.sleep(30)  # Check every 30 seconds

            async with self._batch_lock:
                retry_candidates: list[tuple[str, MeterBatch]] = []
                current_time = datetime.now(timezone.utc)

                for batch_key, batch in self.failed_batches.items():
                    # Skip overflow batches (handled in flush loop)
                    if "_overflow_" in batch_key:
                        continue

                    if not batch.last_attempt:
                        retry_candidates.append((batch_key, batch))
                        continue

                    # Exponential backoff: 1min, 2min, 4min, 8min, ..., max 60min
                    backoff_minutes = min(2 ** (batch.attempt_count - 1), 60)
                    backoff_seconds = backoff_minutes * 60

                    time_since_attempt = (
                        current_time - batch.last_attempt
                    ).total_seconds()
                    if time_since_attempt >= backoff_seconds:
                        retry_candidates.append((batch_key, batch))

            # Retry candidates
            for batch_key, batch in retry_candidates:
                if batch.attempt_count >= self.max_retry_attempts:
                    logger.error(
                        f"Max retries exceeded for {batch.org_uuid}, sending to DLQ"
                    )

                    # Send details to DLQ
                    dlq_event = {
                        "org_uuid": batch.org_uuid,
                        "quantity": batch.total_quantity,
                        "trace_count": len(batch.trace_ids),
                        "trace_ids": list(batch.trace_ids)[:100],  # First 100 traces
                        "error": batch.error,
                        "attempts": batch.attempt_count,
                        "created_at": batch.created_at.isoformat(),
                        "idempotency_key": batch.idempotency_key,
                    }
                    await self._send_to_dlq(dlq_event, "max_retries_exceeded")

                    # Remove from failed batches
                    async with self._batch_lock:
                        self.failed_batches.pop(batch_key, None)
                else:
                    logger.info(
                        f"Retrying batch for {batch.org_uuid} "
                        f"(attempt {batch.attempt_count + 1}/{self.max_retry_attempts})"
                    )

                    success = await self._send_batch_with_rate_limit(batch_key, batch)
                    if success:
                        async with self._batch_lock:
                            self.failed_batches.pop(batch_key, None)
                        logger.info(f"✅ Retry successful for {batch.org_uuid}")

    async def _send_to_dlq(self, event: Any, error: str) -> None:
        """Send failed event to dead letter queue."""
        if not self.dlq_producer:
            logger.error("DLQ producer not initialized")
            return

        try:
            dlq_event = {
                **event,
                "error": error,
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "processor": "stripe_meter",
            }

            await self.dlq_producer.send(
                f"{self.settings.kafka_topic_stripe_ingestion}-dlq", value=dlq_event
            )
            logger.info(f"Sent failed event to DLQ: {event.get('org_uuid', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}", exc_info=True)

    async def _cleanup_processed_traces(self) -> None:
        """Periodically clean up old processed trace IDs to prevent memory growth."""
        while self._running:
            await asyncio.sleep(300)  # Every 5 minutes

            async with self._batch_lock:
                # Keep only last 100k traces
                if len(self.processed_traces) > 100000:
                    # Convert to list, sort by insertion order (not possible with set)
                    # Instead, just clear and start fresh
                    logger.info(
                        f"Clearing processed traces set (was {len(self.processed_traces)} traces)"
                    )
                    self.processed_traces.clear()


# Singleton instance
_stripe_processor_instance: StripeQueueProcessor | None = None


def get_stripe_queue_processor() -> StripeQueueProcessor:
    """Get or create the singleton StripeQueueProcessor instance."""
    global _stripe_processor_instance
    if _stripe_processor_instance is None:
        _stripe_processor_instance = StripeQueueProcessor()
    return _stripe_processor_instance
