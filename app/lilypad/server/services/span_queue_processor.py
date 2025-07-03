"""Span Queue Processor service for consuming spans from Kafka and handling dependency resolution."""

import asyncio
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from uuid import UUID

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from .._utils.opensearch import index_traces_in_opensearch
from .._utils.span_processing import create_span_from_data
from ..db.session import create_session
from ..models.spans import SpanTable
from ..models.users import UserTable
from ..settings import get_settings
from .billing import BillingService
from .opensearch import OpenSearchService
from .projects import ProjectService
from .spans import SpanService
from .stripe_kafka_service import StripeKafkaService

logger = logging.getLogger(__name__)


class TraceBuffer:
    """Buffer for storing spans belonging to a single trace."""

    def __init__(self, trace_id: str, session: Session | None = None) -> None:
        self.trace_id = trace_id
        self.spans: dict[str, dict[str, Any]] = {}  # span_id -> span data
        self.created_at = time.time()
        self._session = session
        # Create instance-specific cache to avoid memory leaks and ensure isolation
        self._parent_cache: dict[str, bool] = {}
        self._max_cache_size = 1000

    def add_span(self, span_data: dict[str, Any]) -> None:
        """Add a span to the buffer."""
        span_id = span_data.get("span_id")
        if span_id:
            self.spans[span_id] = span_data

    @property
    def span_ids(self) -> set[str]:
        """Get all span IDs in the buffer."""
        return set(self.spans.keys())

    def is_complete(self) -> bool:
        """Check if all parent dependencies are satisfied."""
        span_ids = self.span_ids

        for span_data in self.spans.values():
            parent_id = span_data.get("parent_span_id")
            if parent_id and parent_id not in span_ids:
                if self._parent_exists_in_db(parent_id):
                    logger.debug(
                        f"Parent {parent_id} exists in DB for span {span_data.get('span_id')}"
                    )
                    continue

                logger.debug(
                    f"Trace {self.trace_id} incomplete: span {span_data.get('span_id')} "
                    f"waiting for parent {parent_id}"
                )
                return False  # Missing parent
        return True

    def _has_existing_spans_in_db(self) -> bool:
        """Check if this trace already has spans in the database."""
        if not self._session:
            return False

        # Check if any spans exist for this trace_id
        stmt = select(SpanTable).where(SpanTable.trace_id == self.trace_id).limit(1)
        result = self._session.exec(stmt).first()
        exists = result is not None

        return exists

    def _parent_exists_in_db(self, parent_span_id: str) -> bool:
        """Check if a parent span exists in the database."""
        # Check cache first
        if parent_span_id in self._parent_cache:
            return self._parent_cache[parent_span_id]

        if not self._session:
            return False

        # Query database
        stmt = (
            select(SpanTable)
            .where(
                SpanTable.trace_id == self.trace_id, SpanTable.span_id == parent_span_id
            )
            .limit(1)
        )
        result = self._session.exec(stmt).first()
        exists = result is not None

        # Add to cache with size limit
        if len(self._parent_cache) >= self._max_cache_size:
            # Remove oldest entry (FIFO)
            oldest_key = next(iter(self._parent_cache))
            del self._parent_cache[oldest_key]

        self._parent_cache[parent_span_id] = exists
        return exists

    def get_dependency_order(self) -> list[dict[str, Any]]:
        """Get spans in dependency order (parents before children)."""
        ordered = []
        processed = set()

        def process_span(span_id: str) -> None:
            if span_id in processed:
                return

            span_data = self.spans.get(span_id)
            if not span_data:
                return  # pragma: no cover

            # Process parent first
            parent_id = span_data.get("parent_span_id")
            if parent_id and parent_id in self.spans:
                process_span(parent_id)

            # Then process this span
            ordered.append(span_data)
            processed.add(span_id)

        # Start with root spans (no parent)
        root_spans = [
            span_id
            for span_id, span_data in self.spans.items()
            if not span_data.get("parent_span_id")
        ]

        for root_span_id in root_spans:
            process_span(root_span_id)

        # Process any remaining spans (in case of orphaned branches)
        for span_id in self.spans:
            process_span(span_id)

        return ordered


class SpanQueueProcessor:
    """Service for processing spans from Kafka queue with dependency resolution."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.consumer: AIOKafkaConsumer | None = None
        self.trace_buffers: dict[str, TraceBuffer] = {}
        self._running = False
        self._cleanup_task: asyncio.Task | None = None
        self._process_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()  # Async lock for thread-safe access
        # Thread pool for synchronous database operations
        self._executor = ThreadPoolExecutor(
            max_workers=self.settings.kafka_db_thread_pool_size,
            thread_name_prefix="kafka-span-db-worker",
        )
        # Database session and user cache
        self._session: Session | None = None
        self._user_cache: dict[UUID, UserTable] = {}
        logger.info(
            f"Initialized Kafka processor thread pool with {self.settings.kafka_db_thread_pool_size} workers "
            f"for non-blocking DB operations"
        )

    def _get_cached_user(self, user_id: UUID) -> UserTable | None:
        """Get user from cache or database."""
        if user_id in self._user_cache:
            return self._user_cache[user_id]

        if not self._session:
            logger.error("Database session not initialized")
            return None

        result = self._session.exec(select(UserTable).where(UserTable.uuid == user_id))
        user = result.first()

        if user:
            self._user_cache[user_id] = user
            logger.debug(f"Cached user {user_id}")

        return user

    async def initialize(self) -> bool:
        """Initialize Kafka consumer and database session with retry logic."""
        logger.info("[INIT] Starting Kafka consumer initialization")
        logger.info(
            f"[INIT] Bootstrap servers: {self.settings.kafka_bootstrap_servers}"
        )
        logger.info(f"[INIT] Topic: {self.settings.kafka_topic_span_ingestion}")
        logger.info(f"[INIT] Consumer group: {self.settings.kafka_consumer_group}")

        if not self.settings.kafka_bootstrap_servers:
            logger.warning(
                "Kafka not configured (kafka_bootstrap_servers is None), queue processor disabled"
            )
            return False

        # Initialize database session
        try:
            self._session = create_session()
            logger.info("[INIT] Database session initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database session: {e}")
            return False

        # Retry logic for Kafka initialization
        max_retries = 5
        retry_delay = 2  # Start with 2 seconds

        for attempt in range(max_retries):
            try:
                self.consumer = AIOKafkaConsumer(
                    self.settings.kafka_topic_span_ingestion,
                    bootstrap_servers=self.settings.kafka_bootstrap_servers,
                    group_id=self.settings.kafka_consumer_group,
                    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                    key_deserializer=lambda k: k.decode("utf-8") if k else None,
                    enable_auto_commit=True,
                    auto_offset_reset="earliest",
                    max_poll_records=100,
                    session_timeout_ms=30000,
                    heartbeat_interval_ms=10000,
                    retry_backoff_ms=100,
                    request_timeout_ms=40000,  # Increased timeout
                    connections_max_idle_ms=540000,
                )
                logger.info(f"[INIT] Attempt {attempt + 1}: Starting consumer...")
                await self.consumer.start()
                logger.info("[INIT] Consumer started successfully")
                logger.info(
                    f"✅ Kafka consumer initialized - Topic: {self.settings.kafka_topic_span_ingestion}, Group: {self.settings.kafka_consumer_group}"
                )
                return True

            except Exception as e:
                if (
                    "GroupCoordinatorNotAvailableError" in str(e)
                    and attempt < max_retries - 1
                ):
                    logger.warning(
                        f"Kafka not ready yet (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {retry_delay} seconds: {e}"
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(
                        f"Failed to initialize Kafka consumer after {attempt + 1} attempts: {e}"
                    )
                    return False

        return False  # pragma: no cover

    async def start(self) -> None:
        """Start the queue processor."""
        logger.info("[START] Beginning span queue processor startup")
        logger.info("🚀 Starting span queue processor - checking for messages...")

        logger.info("[START] Calling initialize()")
        init_result = await self.initialize()
        logger.info(f"[START] Initialize result: {init_result}")

        if not init_result:
            logger.warning(
                "[START] Queue processor not started due to initialization failure"
            )
            return

        logger.info("[START] Setting _running to True")
        self._running = True

        # Start cleanup task
        logger.info("[START] Creating cleanup task")
        self._cleanup_task = asyncio.create_task(self._cleanup_incomplete_traces())
        logger.info("🧹 Cleanup task started")

        # Start processing task
        logger.info("[START] Creating processing task")
        self._process_task = asyncio.create_task(self._process_queue())
        logger.info("🔄 Processing task started")

        logger.info("[START] All tasks created")
        logger.info("✅ Queue processor fully started - waiting for messages")

    async def stop(self) -> None:
        """Stop the queue processor."""
        logger.info("Stopping queue processor...")
        self._running = False

        # Cancel and wait for cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            logger.info("Cancelling cleanup task...")
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                logger.info("Cleanup task cancelled successfully")
                pass

        # Cancel and wait for process task
        if self._process_task and not self._process_task.done():
            logger.info("Cancelling process task...")
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                logger.info("Process task cancelled successfully")
                pass

        # Stop the consumer
        if self.consumer:
            logger.info("Stopping Kafka consumer...")
            try:
                await self.consumer.stop()
                logger.info("Kafka consumer stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping Kafka consumer: {e}")

        # Close database session
        if self._session:
            logger.info("Closing database session...")
            try:
                self._session.close()
                logger.info("Database session closed successfully")
            except Exception as e:
                logger.error(f"Error closing database session: {e}")
            finally:
                self._session = None

        # Clear user cache
        self._user_cache.clear()
        logger.info("User cache cleared")

        # Shutdown thread pool executor
        logger.info("Shutting down thread pool executor...")
        self._executor.shutdown(wait=True, cancel_futures=False)

        logger.info("Queue processor stopped - processed messages until shutdown")

    async def _process_queue(self) -> None:
        """Main queue processing loop."""
        logger.info("[QUEUE] Entering _process_queue method")
        logger.info("🔄 Starting queue processing loop - polling for messages...")
        poll_count = 0
        logger.info(f"[QUEUE] _running status: {self._running}")
        while self._running:
            try:
                # Fetch messages with timeout
                if poll_count == 0:
                    logger.info("[QUEUE] First poll - calling getmany()")
                records = await self.consumer.getmany(timeout_ms=1000, max_records=100)  # pyright: ignore [reportOptionalMemberAccess]

                poll_count += 1
                if records:
                    msg_count = sum(len(msgs) for msgs in records.values())
                    logger.info(f"📦 Received {msg_count} messages from Kafka queue")
                else:
                    # Log every 10th poll to show it's alive
                    if poll_count % 10 == 0:
                        logger.info(
                            f"🔍 Polling for messages... (poll #{poll_count}, no messages yet)"
                        )

                for _topic_partition, messages in records.items():
                    for record in messages:
                        if not self._running:
                            break  # pragma: no cover
                        logger.info(
                            f"Processing message - Topic: {record.topic}, Partition: {record.partition}, Offset: {record.offset}"
                        )
                        await self._process_message(record)

            except KafkaError as e:
                logger.debug(f"Kafka error in processing loop: {e}")
                await asyncio.sleep(5)  # Back off on error
            except Exception as e:
                logger.debug(f"Unexpected error in processing loop: {e}")
                await asyncio.sleep(5)

    async def _process_message(self, record: Any) -> None:
        """Process a single message from the queue."""
        logger.info(f"_process_message called with record: {record.key}")
        try:
            span_data = record.value
            logger.info(
                f"Processing span data with trace_id: {span_data.get('trace_id')}"
            )
            trace_id = span_data.get("trace_id")

            if not trace_id:
                logger.warning(
                    f"Span missing trace_id, skipping - Span ID: {span_data.get('span_id', 'unknown')}"
                )
                return

            buffer_to_process = None
            force_process_oldest = False

            async with self._lock:
                # Add span to buffer
                if trace_id not in self.trace_buffers:
                    if (
                        len(self.trace_buffers)
                        >= self.settings.kafka_max_concurrent_traces
                    ):
                        # Mark that we need to force process oldest trace
                        force_process_oldest = True

                    self.trace_buffers[trace_id] = TraceBuffer(trace_id, self._session)

                buffer = self.trace_buffers[trace_id]

                # Check span limit per trace
                if len(buffer.spans) >= self.settings.kafka_max_spans_per_trace:
                    logger.warning(
                        f"Trace {trace_id} exceeded max spans limit, processing early"
                    )
                    # Remove buffer while still under lock
                    buffer_to_process = self.trace_buffers.pop(trace_id, None)
                else:
                    buffer.add_span(span_data)
                    span_id = span_data.get("span_id", "unknown")
                    logger.info(
                        f"Added span to buffer - Span ID: {span_id}, Trace ID: {trace_id}, Buffer size: {len(buffer.spans)}"
                    )

                    # Check if trace is complete
                    if buffer.is_complete():
                        logger.info(
                            f"Trace {trace_id} is complete with {len(buffer.spans)} spans, preparing to process"
                        )
                        # Remove buffer while still under lock
                        buffer_to_process = self.trace_buffers.pop(trace_id, None)
                    else:
                        logger.info(
                            f"Trace {trace_id} is not complete yet, buffering span"
                        )

            # Process outside of lock
            if force_process_oldest:
                await self._force_process_oldest_trace()

            if buffer_to_process:
                logger.debug(f"Processing trace {trace_id} outside of lock")
                await self._process_trace(trace_id, buffer_to_process)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

    def _process_trace_sync(
        self, trace_id: str, ordered_spans: list[dict[str, Any]]
    ) -> tuple[list[SpanTable], UUID, UUID, UUID, UUID] | None:
        """Synchronous database operations for processing a trace.

        This method runs in a separate thread to avoid blocking the event loop.
        Uses the class database session and user cache for efficiency.
        """
        if not ordered_spans:
            logger.warning(f"No spans to process for trace {trace_id}")
            return None

        if not self._session:
            logger.error("Database session not initialized")
            return None

        first_span = ordered_spans[0]
        attributes = first_span.get("attributes", {})
        project_uuid_str = attributes.get("lilypad.project.uuid")
        environment_uuid_str = attributes.get("lilypad.environment.uuid")

        if not project_uuid_str:
            logger.warning(
                f"No project UUID found in trace {trace_id}, skipping {len(ordered_spans)} spans"
            )
            return None

        project_uuid = UUID(project_uuid_str)
        environment_uuid = UUID(environment_uuid_str)

        # Extract user_id from first span
        user_id = first_span.get("user_id")
        logger.debug(f"Extracted user_id: {user_id} from trace {trace_id}")
        if not user_id:
            logger.warning(
                f"No user ID found in trace {trace_id}, skipping {len(ordered_spans)} spans"
            )
            return None
        user_id = UUID(user_id)

        logger.debug(f"Processing spans for user: {user_id}")

        # Get user from cache
        user = self._get_cached_user(user_id)
        if not user:
            logger.debug(f"User {user_id} not found for trace {trace_id}")
            return None

        project_service = ProjectService(self._session, user)  # pyright: ignore [reportArgumentType]
        project = project_service.find_record_no_organization(project_uuid)
        logger.debug(f"Found project: {project} for trace {trace_id}")
        if not project:
            logger.warning(
                f"Project {project_uuid} not found, skipping trace {trace_id} with {len(ordered_spans)} spans"
            )
            return None

        # Create span service
        span_service = SpanService(self._session, user)  # pyright: ignore [reportArgumentType]

        # Convert to SpanCreate objects
        span_creates = []
        logger.debug(f"Converting {len(ordered_spans)} spans to SpanCreate objects")
        for span_data in ordered_spans:
            # Remove user_id from span data to avoid storing it
            span_data.pop("user_id", None)
            span_create = asyncio.run(create_span_from_data(span_data))
            span_creates.append(span_create)

        # Create spans in bulk
        spans = span_service.create_bulk_records(
            span_creates,
            project_uuid,
            project.organization_uuid,
        )
        # Don't commit here - will be committed in _process_trace after all operations
        logger.info(
            f"Successfully saved trace to database - Trace ID: {trace_id}, "
            f"Spans: {len(ordered_spans)}, Project: {project_uuid}, User: {user_id}, Environment: {environment_uuid}"
        )
        return spans, project.organization_uuid, user_id, project_uuid, environment_uuid

    async def _process_trace(self, trace_id: str, buffer: TraceBuffer) -> None:
        """Process a complete trace.

        Note: This method should be called after removing the buffer from
        self.trace_buffers while holding the lock.
        """
        logger.info(
            f"Starting to process complete trace - Trace ID: {trace_id}, Spans: {len(buffer.spans)}"
        )

        try:
            # Get spans in dependency order
            ordered_spans = buffer.get_dependency_order()
            logger.debug(f"Ordered spans: {len(ordered_spans)}")
            if not ordered_spans:
                logger.warning(f"No spans to process for trace {trace_id}")
                return

            logger.info(
                f"Processing {len(ordered_spans)} spans in dependency order - Trace ID: {trace_id}"
            )

            # Run synchronous DB operations in thread pool to avoid blocking event loop
            logger.debug(
                f"Processing trace {trace_id} in thread pool to avoid blocking"
            )
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor, self._process_trace_sync, trace_id, ordered_spans
            )
            logger.debug(f"Trace {trace_id} processing completed in thread pool")

            if result:
                spans, org_uuid, user_uuid, project_uuid, environment_uuid = result
                opensearch_service = OpenSearchService()
                if opensearch_service.is_enabled:
                    trace_dicts = [span.model_dump() for span in spans]
                    await index_traces_in_opensearch(
                        project_uuid, environment_uuid, trace_dicts, opensearch_service
                    )
                try:
                    user = self._get_cached_user(user_uuid)

                    if user and self._session:
                        billing_service = BillingService(self._session, user)  # pyright: ignore [reportArgumentType]
                        is_stripe_kafka_enabled = (
                            self.settings.kafka_bootstrap_servers
                            and self.settings.kafka_topic_stripe_ingestion
                            and self.settings.stripe_api_key
                        )
                        stripe_kafka_service = (
                            StripeKafkaService(user)  # pyright: ignore [reportArgumentType]
                            if is_stripe_kafka_enabled
                            else None
                        )
                        await billing_service.report_span_usage_with_fallback(
                            org_uuid, len(spans), stripe_kafka_service
                        )
                        logger.debug(  # pragma: no cover
                            f"Successfully reported {len(spans)} spans for billing"
                        )
                except Exception as e:
                    # if reporting fails, we don't want to fail the entire span creation
                    logger.error(f"Error reporting span usage: {e}")

                # Commit the session after all operations are complete
                if self._session:
                    self._session.commit()
                    logger.debug(f"Transaction committed for trace {trace_id}")

        except IntegrityError as e:
            if self._session:
                self._session.rollback()
            logger.error(
                f"Integrity error processing trace {trace_id}: {e}. Likely parent span missing."
            )
        except Exception as e:
            if self._session:
                self._session.rollback()
            logger.error(f"Error processing trace {trace_id}: {e}")

    async def _cleanup_incomplete_traces(self) -> None:
        """Periodically cleanup incomplete traces that have timed out."""
        logger.info("[CLEANUP] Cleanup task started")
        while self._running:
            try:
                logger.info(
                    f"[CLEANUP] Sleeping for {self.settings.kafka_cleanup_interval_seconds} seconds"
                )
                await asyncio.sleep(self.settings.kafka_cleanup_interval_seconds)

                current_time = time.time()
                traces_to_process = []

                async with self._lock:
                    for trace_id, buffer in list(self.trace_buffers.items()):
                        age = current_time - buffer.created_at
                        if age > self.settings.kafka_buffer_ttl_seconds:
                            traces_to_process.append(trace_id)

                for trace_id in traces_to_process:
                    logger.warning(
                        f"Force processing incomplete trace {trace_id} due to timeout"
                    )
                    await self._force_process_incomplete_trace(trace_id)

            except Exception as e:
                logger.debug(f"Error in cleanup task: {e}")

    async def _force_process_incomplete_trace(self, trace_id: str) -> None:
        """Force process an incomplete trace by setting missing parents to null."""
        buffer_to_process = None

        async with self._lock:
            buffer = self.trace_buffers.get(trace_id)
            if not buffer:
                return

            # Update spans with missing parents
            span_ids = buffer.span_ids
            for span_data in buffer.spans.values():
                parent_id = span_data.get("parent_span_id")
                if parent_id and parent_id not in span_ids:
                    if buffer._parent_exists_in_db(parent_id):
                        logger.info(
                            f"Parent {parent_id} found in DB for span {span_data.get('span_id')}, "
                            f"keeping parent_span_id"
                        )
                    else:
                        logger.warning(
                            f"Setting missing parent {parent_id} to null for span {span_data.get('span_id')} "
                            f"in trace {trace_id} - parent not found in buffer or DB"
                        )
                        span_data["parent_span_id"] = None

            # Remove buffer while still under lock
            buffer_to_process = self.trace_buffers.pop(trace_id, None)

        # Now process the trace outside of lock
        if buffer_to_process:
            await self._process_trace(trace_id, buffer_to_process)

    async def _force_process_oldest_trace(self) -> None:
        """Force process the oldest trace to make room for new ones."""
        if not self.trace_buffers:
            return

        # Find oldest trace
        oldest_trace_id = min(
            self.trace_buffers.keys(),
            key=lambda tid: self.trace_buffers[tid].created_at,
        )

        logger.warning(f"Force processing oldest trace {oldest_trace_id} to make room")
        await self._force_process_incomplete_trace(oldest_trace_id)


# Singleton instance
_processor_instance: SpanQueueProcessor | None = None


def get_span_queue_processor() -> SpanQueueProcessor:
    """Get or create the singleton SpanQueueProcessor instance."""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = SpanQueueProcessor()
    return _processor_instance
