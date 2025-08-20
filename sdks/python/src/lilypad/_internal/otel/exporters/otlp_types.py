"""Type aliases for OTLP (OpenTelemetry Protocol) types.

This module provides convenient aliases for the Fern-generated OTLP types,
making them easier to work with while maintaining type safety.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lilypad._generated.telemetry import (  # noqa: PLC2701
        TelemetrySendTracesRequestResourceSpansItem as ResourceSpans,
        TelemetrySendTracesRequestResourceSpansItemResource as Resource,
        TelemetrySendTracesRequestResourceSpansItemResourceAttributesItem as ResourceAttribute,
        TelemetrySendTracesRequestResourceSpansItemScopeSpansItem as ScopeSpans,
        TelemetrySendTracesRequestResourceSpansItemScopeSpansItemScope as InstrumentationScope,
        TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItem as Span,
        TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItemAttributesItem as SpanAttribute,
        TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItemAttributesItemValue as AttributeValue,
        TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItemStatus as SpanStatus,
        TelemetrySendTracesResponse as TraceResponse,
    )

    # Re-export with cleaner names
    __all__ = [
        "AttributeValue",
        "InstrumentationScope",
        "Resource",
        "ResourceAttribute",
        "ResourceSpans",
        "ScopeSpans",
        "Span",
        "SpanAttribute",
        "SpanStatus",
        "TraceResponse",
    ]
