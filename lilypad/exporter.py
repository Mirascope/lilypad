"""Custom span exporter that sends spans to a custom endpoint as JSON."""

import json
from collections.abc import Sequence

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import (
    SpanExporter,
    SpanExportResult,
)
from rich import print

from lilypad.models import SpanPublic
from lilypad.server.client import LilypadClient


class JSONSpanExporter(SpanExporter):
    """A custom span exporter that sends spans to a custom endpoint as JSON."""

    def __init__(self, base_url: str) -> None:
        """Initialize the exporter with the custom endpoint URL."""
        self.client = LilypadClient(base_url, timeout=10)

    def pretty_print_display_names(self, spans: Sequence[SpanPublic]) -> None:
        """Extract and pretty print the display_name attribute from each span, handling nested spans."""
        for span in spans:
            self._print_span_node(span, indent=0)

    def _print_span_node(self, span: SpanPublic, indent: int) -> None:
        """Recursively print a SpanNode and its children with indentation."""
        indent_str = "    " * indent  # 4 spaces per indent level

        print(f"{indent_str}{span.display_name}")  # noqa: T201

        for child in span.child_spans:
            self._print_span_node(child, indent + 1)

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Convert spans to a list of JSON serializable dictionaries"""
        span_data = [self._span_to_dict(span) for span in spans]
        json_data = json.dumps(span_data)

        try:
            response_spans = self.client.post_traces(data=json_data)
            if response_spans:
                self.pretty_print_display_names(response_spans)
                return SpanExportResult.SUCCESS
            else:
                return SpanExportResult.FAILURE
        except Exception as e:
            print(f"Error sending spans: {e}")
            return SpanExportResult.FAILURE

    def _span_to_dict(self, span: ReadableSpan) -> dict:
        """Convert the span data to a dictionary that can be serialized to JSON"""
        # span.instrumentation_scope to_json does not work
        instrumentation_scope = (
            {
                "name": span.instrumentation_scope.name,
                "version": span.instrumentation_scope.version,
                "schema_url": span.instrumentation_scope.schema_url,
                "attributes": dict(span.instrumentation_scope.attributes.items())
                if span.instrumentation_scope.attributes
                else None,
            }
            if span.instrumentation_scope
            else {
                "name": None,
                "version": None,
                "schema_url": None,
                "attributes": None,
            }
        )
        return {
            "trace_id": f"{span.context.trace_id:032x}" if span.context else None,
            "span_id": f"{span.context.span_id:016x}" if span.context else None,
            "parent_span_id": f"{span.parent.span_id:016x}" if span.parent else None,
            "instrumentation_scope": instrumentation_scope,
            "resource": span.resource.to_json(0),
            "name": span.name,
            "start_time": span.start_time,
            "end_time": span.end_time,
            "attributes": dict(span.attributes.items()) if span.attributes else None,
            "status": span.status.status_code.name,
            "events": [
                {
                    "name": event.name,
                    "attributes": event.attributes,
                    "timestamp": event.timestamp,
                }
                for event in span.events
            ],
            "links": [
                {
                    "context": {
                        "trace_id": f"{link.context.trace_id:032}",
                        "span_id": f"{link.context.span_id:016x}",
                    },
                    "attributes": link.attributes,
                }
                for link in span.links
            ],
        }
