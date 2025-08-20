"""Type definitions for the two-phase export system.

This module defines the event types and data structures used for
immediate start event transmission and batched end event export.
"""

from enum import Enum
from typing import TypedDict, Literal

from opentelemetry.util.types import AttributeValue


SpanKindLiteral = Literal["CLIENT", "SERVER", "PRODUCER", "CONSUMER", "INTERNAL"]
StatusCode = Literal["UNSET", "OK", "ERROR"]


class SpanEventType(Enum):
    """Event types for span lifecycle tracking."""

    SPAN_STARTED = "span_started"
    SPAN_UPDATED = "span_updated"
    SPAN_COMPLETED = "span_completed"


class SpanEvent(TypedDict):
    """Individual event within a span."""

    name: str
    timestamp: int
    """Nanoseconds since epoch (OTel standard)."""
    attributes: dict[str, AttributeValue]


class Status(TypedDict):
    """Status representation for serialization."""

    code: StatusCode
    description: str | None


class SpanContextDict(TypedDict):
    """Span context for links and parent references."""

    trace_id: str
    span_id: str
    trace_flags: int
    trace_state: str | None


class Link(TypedDict):
    """Link representation for span relationships."""

    context: SpanContextDict
    attributes: dict[str, AttributeValue]


class SpanStartEvent(TypedDict):
    """Minimal span data for immediate transmission.

    This event is sent immediately when a span starts to provide
    real-time visibility into long-running operations.
    """

    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    start_time: int
    """Nanoseconds since epoch."""
    kind: SpanKindLiteral
    attributes: dict[str, AttributeValue]
    """Minimal required attributes only."""


class SpanUpdateEvent(TypedDict, total=False):
    """Incremental updates to span data.

    These events are batched and sent periodically to update
    span attributes or add events without waiting for completion.
    """

    trace_id: str
    span_id: str
    timestamp: int
    """Nanoseconds since epoch."""
    attributes: dict[str, AttributeValue]
    events: list[SpanEvent]


class SpanCompleteEvent(TypedDict):
    """Complete span data for batch export.

    This event contains all span data and is sent when the span
    completes, typically in batches for efficiency.
    """

    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    kind: SpanKindLiteral
    start_time: int
    """Nanoseconds since epoch."""
    end_time: int
    """Nanoseconds since epoch."""
    status: Status
    attributes: dict[str, AttributeValue]
    events: list[SpanEvent]
    links: list[Link]


class GenAIEventNames:
    """Standard event names for GenAI spans.

    These follow OpenTelemetry semantic conventions for GenAI.
    """

    PROMPT = "gen_ai.content.prompt"
    COMPLETION = "gen_ai.content.completion"
    TOOL_CALL = "gen_ai.tool_call"
    TOOL_RESULT = "gen_ai.tool_result"
