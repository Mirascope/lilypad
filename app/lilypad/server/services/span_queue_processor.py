"""Span Queue Processor service for consuming spans from Kafka and handling dependency resolution."""

import asyncio
import contextlib
import json
import logging
import time
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from kafka import KafkaConsumer  # type: ignore
from kafka.errors import KafkaError  # type: ignore

from ..db.session import get_session
from ..models.users import UserTable
from ..schemas.spans import SpanCreate
from ..settings import get_settings
from .billing import BillingService
from .projects import ProjectService
from .spans import SpanService

logger = logging.getLogger(__name__)


class TraceBuffer:
    """Buffer for storing spans belonging to a single trace."""

    def __init__(self, trace_id: str) -> None:
        self.trace_id = trace_id
        self.spans: dict[str, dict[str, Any]] = {}  # span_id -> span data
        self.created_at = time.time()

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
                return False  # Missing parent
        return True

    def get_dependency_order(self) -> list[dict[str, Any]]:
        """Get spans in dependency order (parents before children)."""
        ordered = []
        processed = set()

        def process_span(span_id: str) -> None:
            if span_id in processed:
                return

            span_data = self.spans.get(span_id)
            if not span_data:
                return

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
        self.consumer: KafkaConsumer | None = None
        self.trace_buffers: dict[str, TraceBuffer] = {}
        self._running = False
        self._cleanup_task: asyncio.Task | None = None

    def initialize(self) -> bool:
        """Initialize Kafka consumer."""
        if not self.settings.kafka_bootstrap_servers:
            logger.info("Kafka not configured, queue processor disabled")
            return False

        try:
            self.consumer = KafkaConsumer(
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
            )
            logger.info("Kafka consumer initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {e}")
            return False

    async def start(self) -> None:
        """Start the queue processor."""
        if not self.initialize():
            logger.warning("Queue processor not started due to initialization failure")
            return

        self._running = True

        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_incomplete_traces())

        # Start processing in background
        asyncio.create_task(self._process_queue())

        logger.info("Queue processor started")

    async def stop(self) -> None:
        """Stop the queue processor."""
        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task

        if self.consumer:
            self.consumer.close()

        logger.info("Queue processor stopped")

    async def _process_queue(self) -> None:
        """Main queue processing loop."""
        while self._running:
            try:
                # Poll for messages
                messages = self.consumer.poll(timeout_ms=1000)

                for _topic_partition, records in messages.items():
                    for record in records:
                        await self._process_message(record)

            except KafkaError as e:
                logger.error(f"Kafka error in processing loop: {e}")
                await asyncio.sleep(5)  # Back off on error
            except Exception as e:
                logger.error(f"Unexpected error in processing loop: {e}")
                await asyncio.sleep(5)

    async def _process_message(self, record: Any) -> None:
        """Process a single message from the queue."""
        try:
            span_data = record.value
            trace_id = span_data.get("trace_id")

            if not trace_id:
                logger.warning("Span missing trace_id, skipping")
                return

            # Add span to buffer
            if trace_id not in self.trace_buffers:
                if len(self.trace_buffers) >= self.settings.kafka_max_concurrent_traces:
                    # Force process oldest trace to make room
                    await self._force_process_oldest_trace()

                self.trace_buffers[trace_id] = TraceBuffer(trace_id)

            buffer = self.trace_buffers[trace_id]

            # Check span limit per trace
            if len(buffer.spans) >= self.settings.kafka_max_spans_per_trace:
                logger.warning(
                    f"Trace {trace_id} exceeded max spans limit, processing early"
                )
                await self._process_trace(trace_id)
                return

            buffer.add_span(span_data)

            # Check if trace is complete
            if buffer.is_complete():
                await self._process_trace(trace_id)

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _process_trace(self, trace_id: str) -> None:
        """Process a complete trace."""
        buffer = self.trace_buffers.get(trace_id)
        if not buffer:
            return

        try:
            # Get spans in dependency order
            ordered_spans = buffer.get_dependency_order()

            if not ordered_spans:
                logger.warning(f"No spans to process for trace {trace_id}")
                return

            # Extract project UUID from first span
            first_span = ordered_spans[0]
            attributes = first_span.get("attributes", {})
            project_uuid_str = attributes.get("lilypad.project.uuid")

            if not project_uuid_str:
                logger.error(f"No project UUID found in trace {trace_id}")
                return

            project_uuid = UUID(project_uuid_str)

            # Create spans in database
            # Using synchronous session since we're in an async context
            for session in get_session():
                # Get system user for span creation
                system_user = (
                    session.query(UserTable)
                    .filter(UserTable.email == "system@lilypad.com")
                    .first()
                )

                if not system_user:
                    logger.error("System user not found")
                    return

                # Get project and organization
                project_service = ProjectService(session, system_user)
                project = project_service.find_record_no_organization(project_uuid)
                if not project:
                    logger.error(f"Project {project_uuid} not found")
                    return

                # Create span service
                span_service = SpanService(session, system_user)

                # Convert to SpanCreate objects
                span_creates = []
                for span_data in ordered_spans:
                    # Process span data similar to the original _process_span function
                    span_create = self._convert_to_span_create(span_data)
                    span_creates.append(span_create)

                # Determine if we need billing service
                billing_service = None
                if self.settings.stripe_api_key:
                    billing_service = BillingService(session, system_user)

                # Create spans in bulk
                span_service.create_bulk_records(
                    span_creates,
                    billing_service,
                    project_uuid,
                    project.organization_uuid,
                )

                break  # Exit after first iteration

            logger.info(
                f"Successfully processed trace {trace_id} with {len(ordered_spans)} spans"
            )

        except IntegrityError as e:
            logger.error(f"Database integrity error processing trace {trace_id}: {e}")
        except Exception as e:
            logger.error(f"Error processing trace {trace_id}: {e}")
        finally:
            # Remove from buffer
            self.trace_buffers.pop(trace_id, None)

    def _convert_to_span_create(self, span_data: dict[str, Any]) -> SpanCreate:
        """Convert raw span data to SpanCreate object."""
        # This mirrors the logic from _process_span in traces_api.py
        attributes = span_data.get("attributes", {})

        # Calculate cost and tokens (simplified for now)
        cost = span_data.get("cost", 0)
        input_tokens = span_data.get("input_tokens")
        output_tokens = span_data.get("output_tokens")

        # Extract function UUID
        function_uuid_str = attributes.get("lilypad.function.uuid")

        return SpanCreate(
            span_id=span_data["span_id"],
            type=attributes.get("lilypad.type"),
            function_uuid=UUID(function_uuid_str) if function_uuid_str else None,
            scope=span_data.get("scope", "llm"),
            data=span_data,
            parent_span_id=span_data.get("parent_span_id"),
            cost=cost,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=span_data.get("duration_ms", 0),
        )

    async def _cleanup_incomplete_traces(self) -> None:
        """Periodically cleanup incomplete traces that have timed out."""
        while self._running:
            try:
                await asyncio.sleep(self.settings.kafka_cleanup_interval_seconds)

                current_time = time.time()
                traces_to_process = []

                for trace_id, buffer in list(self.trace_buffers.items()):
                    age = current_time - buffer.created_at
                    if age > self.settings.kafka_buffer_ttl_seconds:
                        traces_to_process.append(trace_id)

                for trace_id in traces_to_process:
                    logger.warning(
                        f"Force processing incomplete trace {trace_id} due to timeout"
                    )
                    await self._force_process_incomplete_trace(trace_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    async def _force_process_incomplete_trace(self, trace_id: str) -> None:
        """Force process an incomplete trace by setting missing parents to null."""
        buffer = self.trace_buffers.get(trace_id)
        if not buffer:
            return

        # Update spans with missing parents
        span_ids = buffer.span_ids
        for span_data in buffer.spans.values():
            parent_id = span_data.get("parent_span_id")
            if parent_id and parent_id not in span_ids:
                logger.warning(
                    f"Setting missing parent {parent_id} to null for span {span_data.get('span_id')}"
                )
                span_data["parent_span_id"] = None

        # Now process the trace
        await self._process_trace(trace_id)

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
