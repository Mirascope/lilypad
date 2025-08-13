"""Types for OpenTelemetry provider-agnostic LLM handling."""

from typing import Literal
from typing_extensions import Required, TypedDict


class LLMOpenTelemetryFunctionCall(TypedDict):
    arguments: str
    """The arguments of the function call as a JSON string."""

    name: str
    """The name of the function to call."""


class LLMOpenTelemetryToolCall(TypedDict):
    """A provider-agnostic type for tool call parameters."""

    id: str
    """The ID of the tool call."""

    type: Literal["function"]
    """The discriminated union type "tool_call" for this type."""

    function: LLMOpenTelemetryFunctionCall
    """The function call"""


class LLMOpenTelemetryMessage(TypedDict, total=False):
    """A provider-agnostic type for message parameters."""

    role: Required[str]
    """The role of the message."""

    content: str
    """The content of the message."""

    tool_calls: list[LLMOpenTelemetryToolCall]
    """The list of tool calls, if any."""
