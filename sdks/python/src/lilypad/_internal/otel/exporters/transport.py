"""Transport implementation for OpenTelemetry exporters.

This module provides the transport layer for sending OpenTelemetry span
events to the Lilypad ingestion endpoint. It wraps the Fern-generated
LilypadClient to provide the interface needed by OpenTelemetry exporters.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .otlp_protocols import AttributeValueType

from lilypad._generated.client import Lilypad  # noqa: PLC2701
from lilypad._generated.telemetry import (  # noqa: PLC2701
    TelemetrySendTracesRequestResourceSpansItem,
    TelemetrySendTracesRequestResourceSpansItemResource,
    TelemetrySendTracesRequestResourceSpansItemResourceAttributesItem,
    TelemetrySendTracesRequestResourceSpansItemResourceAttributesItemValue,
    TelemetrySendTracesRequestResourceSpansItemScopeSpansItem,
    TelemetrySendTracesRequestResourceSpansItemScopeSpansItemScope,
    TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItem,
    TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItemAttributesItem,
    TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItemAttributesItemValue,
    TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItemStatus,
)
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExportResult


class TransportError(Exception):
    """Base exception for transport-related errors."""

    pass


class NetworkError(TransportError):
    """Network-related transport errors."""

    pass


class RateLimitError(TransportError):
    """Rate limiting errors from the server.

    Attributes:
        retry_after: Optional seconds to wait before retrying
    """

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


@dataclass
class TelemetryConfig:
    """Configuration for telemetry export behavior.

    Attributes:
        timeout: Request timeout in seconds for telemetry operations.
        max_retry_attempts: Maximum number of retry attempts for failed exports.
    """

    timeout: float = 30.0
    max_retry_attempts: int = 3


class TelemetryTransport:
    """Transport layer for OpenTelemetry spans using Fern client.

    This transport accepts standard OpenTelemetry ReadableSpan objects
    and converts them to OTLP format for transmission via the Fern client.
    """

    def __init__(
        self,
        client: Lilypad,
        config: TelemetryConfig | None = None,
    ) -> None:
        """Initialize the telemetry transport.

        Args:
            client: The Fern-generated Lilypad client instance.
                    In the future, this will accept the enhanced client from lilypad.client
                    that provides error handling and caching capabilities.
            config: Optional telemetry-specific configuration.
        """
        self.client = client
        self.config = config or TelemetryConfig()

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export a batch of spans to the telemetry endpoint.

        This is the standard OpenTelemetry export interface.

        Args:
            spans: Sequence of ReadableSpan objects to export.

        Returns:
            SpanExportResult indicating success or failure.
        """
        if not spans:
            return SpanExportResult.SUCCESS

        try:
            otlp_data = self._convert_spans_to_otlp(spans)

            if not hasattr(self.client, "telemetry"):
                import logging

                logger = logging.getLogger(__name__)
                logger.warning("Lilypad client does not have telemetry endpoint")
                return SpanExportResult.SUCCESS

            response = self.client.telemetry.send_traces(resource_spans=otlp_data)

            if (
                response
                and hasattr(response, "partial_success")
                and response.partial_success
            ):
                partial_success = response.partial_success
                if hasattr(partial_success, "rejected_spans"):
                    rejected = partial_success.rejected_spans
                    if rejected is not None and rejected > 0:
                        return SpanExportResult.FAILURE

            return SpanExportResult.SUCCESS

        except Exception as e:
            import logging
            import traceback

            logger = logging.getLogger(__name__)
            logger.error(f"Failed to export spans: {e}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            return SpanExportResult.FAILURE

    def _convert_spans_to_otlp(self, spans: Sequence[ReadableSpan]) -> list:
        """Convert OpenTelemetry spans to OTLP format.

        Args:
            spans: Sequence of ReadableSpan objects.

        Returns:
            List of ResourceSpans in OTLP format.
        """
        resource_spans_map = {}

        for span in spans:
            resource_key = id(span.resource) if span.resource else "default"

            if resource_key not in resource_spans_map:
                resource = None
                if span.resource:
                    resource_attrs = []
                    for key, value in span.resource.attributes.items():
                        attr_value = self._convert_resource_attribute_value(value)
                        resource_attrs.append(
                            TelemetrySendTracesRequestResourceSpansItemResourceAttributesItem(
                                key=key,
                                value=attr_value,
                            )
                        )
                    resource = TelemetrySendTracesRequestResourceSpansItemResource(
                        attributes=resource_attrs
                    )

                resource_spans_map[resource_key] = {
                    "resource": resource,
                    "scope_spans": {},
                }

            scope_key = (
                span.instrumentation_scope.name
                if span.instrumentation_scope
                else "unknown"
            )

            if scope_key not in resource_spans_map[resource_key]["scope_spans"]:
                scope = None
                if span.instrumentation_scope:
                    scope = (
                        TelemetrySendTracesRequestResourceSpansItemScopeSpansItemScope(
                            name=span.instrumentation_scope.name,
                            version=span.instrumentation_scope.version,
                        )
                    )

                resource_spans_map[resource_key]["scope_spans"][scope_key] = {
                    "scope": scope,
                    "spans": [],
                }

            otlp_span = self._convert_span(span)
            resource_spans_map[resource_key]["scope_spans"][scope_key]["spans"].append(
                otlp_span
            )

        result = []
        for resource_data in resource_spans_map.values():
            scope_spans = []
            for scope_data in resource_data["scope_spans"].values():
                scope_spans.append(
                    TelemetrySendTracesRequestResourceSpansItemScopeSpansItem(
                        scope=scope_data["scope"],
                        spans=scope_data["spans"],
                    )
                )

            result.append(
                TelemetrySendTracesRequestResourceSpansItem(
                    resource=resource_data["resource"],
                    scope_spans=scope_spans,
                )
            )

        return result

    def _convert_span(
        self, span: ReadableSpan
    ) -> TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItem:
        """Convert a single ReadableSpan to OTLP format."""

        attributes = []
        if span.attributes:
            for key, value in span.attributes.items():
                attr_value = self._convert_attribute_value(value)
                attributes.append(
                    TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItemAttributesItem(
                        key=key,
                        value=attr_value,
                    )
                )

        status = None
        if span.status:
            status = TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItemStatus(
                code=span.status.status_code.value,
                message=span.status.description or "",
            )

        context = span.get_span_context()
        if not context:
            trace_id = "00000000000000000000000000000000"
            span_id = "0000000000000000"
        else:
            trace_id = format(context.trace_id, "032x")
            span_id = format(context.span_id, "016x")

        kwargs = {
            "trace_id": trace_id,
            "span_id": span_id,
            "name": span.name,
            "kind": span.kind.value if span.kind else 0,
            "start_time_unix_nano": str(span.start_time) if span.start_time else "0",
            "end_time_unix_nano": str(span.end_time) if span.end_time else "0",
        }

        if attributes:
            kwargs["attributes"] = attributes

        if span.parent and span.parent.span_id:
            kwargs["parent_span_id"] = format(span.parent.span_id, "016x")

        if status:
            kwargs["status"] = status

        return TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItem(
            **kwargs
        )

    def _convert_attribute_value(
        self, value: AttributeValueType
    ) -> TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItemAttributesItemValue:
        """Convert Python value to OTLP AttributeValue for span attributes."""

        if isinstance(value, bool):
            return TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItemAttributesItemValue(
                bool_value=value
            )
        elif isinstance(value, int):
            return TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItemAttributesItemValue(
                int_value=str(value)
            )
        elif isinstance(value, float):
            return TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItemAttributesItemValue(
                double_value=value
            )
        elif isinstance(value, str):
            return TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItemAttributesItemValue(
                string_value=value
            )
        elif isinstance(value, Sequence) and not isinstance(value, str):
            return TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItemAttributesItemValue(
                string_value=str(list(value))
            )
        else:
            return TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItemAttributesItemValue(
                string_value=str(value)
            )

    def _convert_resource_attribute_value(
        self, value: AttributeValueType
    ) -> TelemetrySendTracesRequestResourceSpansItemResourceAttributesItemValue:
        """Convert Python value to OTLP AttributeValue for resource attributes."""
        if isinstance(value, bool):
            return (
                TelemetrySendTracesRequestResourceSpansItemResourceAttributesItemValue(
                    bool_value=value
                )
            )
        elif isinstance(value, int):
            return (
                TelemetrySendTracesRequestResourceSpansItemResourceAttributesItemValue(
                    int_value=str(value)
                )
            )
        elif isinstance(value, float):
            return (
                TelemetrySendTracesRequestResourceSpansItemResourceAttributesItemValue(
                    double_value=value
                )
            )
        elif isinstance(value, str):
            return (
                TelemetrySendTracesRequestResourceSpansItemResourceAttributesItemValue(
                    string_value=value
                )
            )
        elif isinstance(value, Sequence) and not isinstance(value, str):
            return (
                TelemetrySendTracesRequestResourceSpansItemResourceAttributesItemValue(
                    string_value=str(list(value))
                )
            )
        else:
            return (
                TelemetrySendTracesRequestResourceSpansItemResourceAttributesItemValue(
                    string_value=str(value)
                )
            )

    def shutdown(self) -> None:
        """Shutdown the transport and clean up resources."""
        pass
