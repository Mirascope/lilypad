"""Types for OpenTelemetry provider-agnostic LLM handling."""

from typing import Literal, Protocol
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


class LLMOpenTelemetryInlineData(TypedDict, total=False):
    """A provider-agnostic type for data parameters."""

    data: str
    """The data should be base64 encoded."""

    mime_type: str
    """The mime type of the data."""


class LLMOpenTelemetryMessage(TypedDict, total=False):
    """A provider-agnostic type for message parameters."""

    role: Required[str]
    """The role of the message."""

    content: str
    """The content of the message."""

    tool_calls: list[LLMOpenTelemetryToolCall]
    """The list of tool calls, if any."""

    inline_data: list[LLMOpenTelemetryInlineData]
    """The list of data to be embedded in the message, if any."""


class ToolCallFunctionProtocol(Protocol):
    """Protocol for tool call function objects."""

    @property
    def name(self) -> str | None: ...

    @property
    def arguments(self) -> str | None: ...


class ToolCallProtocol(Protocol):
    """Protocol for tool call objects."""

    @property
    def id(self) -> str | None: ...

    @property
    def index(self) -> int: ...

    @property
    def function(self) -> ToolCallFunctionProtocol | None: ...
