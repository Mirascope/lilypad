"""Exporters for span data transmission.

This module provides exporters for the two-phase export system:
- ImmediateStartExporter for fast start event transmission
- LilypadOTLPExporter for batched OTLP/HTTP export
"""

from collections.abc import Sequence

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from .transport import TelemetryTransport


class ImmediateStartExporter:
    """Lightweight exporter for immediate start events.

    This exporter is optimized for low-latency transmission of
    minimal span start events. It's not a full SpanExporter as
    it only handles start events, not complete spans.

    The exporter uses a best-effort approach - failures don't
    block the application and are logged for monitoring.

    Attributes:
        transport: Transport client for sending events.
        max_retry_attempts: Maximum number of retry attempts.
        retry_delay: Base delay for exponential backoff.
    """

    def __init__(self, transport: TelemetryTransport, max_retry_attempts: int = 3):
        """Initialize the start exporter.

        Args:
            transport: Transport client for sending events.
            max_retry_attempts: Maximum retry attempts for failed sends.
        """
        self.transport = transport
        self.max_retry_attempts = max_retry_attempts
        self.retry_delay = 0.1  # Base delay for exponential backoff
        self._shutdown = False

    def export_start_event(self, span: ReadableSpan) -> bool:
        """Export a start event with retry logic.

        This method attempts to send the start event with exponential
        backoff retry logic. Failures are logged but don't raise
        exceptions to avoid blocking the application.

        Args:
            span: The span that just started.

        Returns:
            True if the event was sent successfully, False otherwise.
        """
        # Implementation will extract start event data from span
        # and send via transport.export() with special flag
        raise NotImplementedError()

    def shutdown(self) -> None:
        """Mark the exporter as shutdown.

        After shutdown, the exporter will not send any more events.
        """
        self._shutdown = True


class LilypadOTLPExporter(SpanExporter):
    """OTLP/HTTP exporter for completed spans.

    This exporter implements the OpenTelemetry SpanExporter interface
    for exporting completed spans in OTLP format over HTTP. It's
    designed to work with BatchSpanProcessor for efficient batching.

    Attributes:
        transport: Transport client for sending events.
        timeout: Request timeout in seconds.
    """

    def __init__(self, transport: TelemetryTransport, timeout: float = 30.0):
        """Initialize the OTLP exporter.

        Args:
            transport: Transport client for sending events.
            timeout: Request timeout in seconds.
        """
        self.transport = transport
        self.timeout = timeout

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export completed spans in OTLP format.

        This method is called by BatchSpanProcessor with a batch
        of completed spans to export.

        Args:
            spans: Sequence of completed spans to export.

        Returns:
            SpanExportResult indicating success or failure.
        """
        # Delegate to transport which handles OTLP conversion
        return self.transport.export(spans)

    def shutdown(self) -> None:
        """Clean up exporter resources.

        This method is called when the exporter is no longer needed
        and should clean up any resources.
        """
        self.transport.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush any pending data.

        Args:
            timeout_millis: Maximum time to wait in milliseconds.

        Returns:
            True if flush completed successfully.
        """
        return True
