"""Span processors for two-phase export system.

This module implements a custom SpanProcessor that sends immediate
start events and batches end events for efficient export.
"""

from concurrent.futures import ThreadPoolExecutor

from opentelemetry.context import Context
from opentelemetry.sdk.trace import SpanProcessor, ReadableSpan
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .types import SpanStartEvent
from .exporters import ImmediateStartExporter


class LLMSpanProcessor(SpanProcessor):
    """Two-phase span processor for LLM tracing.

    This processor implements a two-phase export strategy:
    1. Immediate transmission of minimal start events for real-time visibility
    2. Batched transmission of complete events for efficiency

    The processor uses a thread pool to ensure start events don't block
    the application while maintaining compatibility with OpenTelemetry's
    synchronous SDK.

    Attributes:
        start_exporter: Exporter for immediate start events.
        batch_processor: Standard batch processor for completed spans.
        executor: Thread pool for non-blocking start event transmission.
    """

    def __init__(
        self,
        start_exporter: ImmediateStartExporter,
        batch_processor: BatchSpanProcessor | None = None,
        executor: ThreadPoolExecutor | None = None,
    ):
        """Initialize the two-phase processor.

        Args:
            start_exporter: Exporter for immediate start events.
            batch_processor: Optional batch processor for end events.
            executor: Optional thread pool executor (creates default if None).
        """
        self.start_exporter = start_exporter
        self.batch_processor = batch_processor
        self.executor = executor or ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="llm-span-processor"
        )
        self._shutdown = False

    def on_start(
        self, span: ReadableSpan, parent_context: Context | None = None
    ) -> None:
        """Handle span start by sending immediate start event.

        This method extracts minimal span data and sends it immediately
        via the start exporter in a non-blocking manner.

        Args:
            span: The span that just started.
            parent_context: Optional parent context for the span.
        """
        if self._shutdown:
            return

        # Note: _create_start_event is not implemented yet
        # For now, pass the span directly to export_start_event
        self.executor.submit(self.start_exporter.export_start_event, span)

    def on_end(self, span: ReadableSpan) -> None:
        """Handle span end by delegating to batch processor.

        Args:
            span: The span that just ended.
        """
        if self.batch_processor and not self._shutdown:
            self.batch_processor.on_end(span)

    def shutdown(self) -> None:
        """Gracefully shutdown the processor.

        This ensures all pending start events are sent and the
        batch processor is properly shutdown.
        """
        self._shutdown = True

        if self.batch_processor:
            self.batch_processor.shutdown()

        self.executor.shutdown(wait=True)
        self.start_exporter.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush all pending data.

        Args:
            timeout_millis: Maximum time to wait in milliseconds.

        Returns:
            True if flush completed successfully.
        """
        if self.batch_processor:
            return self.batch_processor.force_flush(timeout_millis)
        return True

    def _create_start_event(
        self, span: ReadableSpan, parent_context: Context | None
    ) -> SpanStartEvent:
        """Extract minimal span data for start event.

        Args:
            span: The span to extract data from.
            parent_context: Optional parent context.

        Returns:
            SpanStartEvent with minimal required data.
        """
        raise NotImplementedError()
