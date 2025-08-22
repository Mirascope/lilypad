"""Types for OpenTelemetry provider-agnostic LLM handling."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, fields
from types import TracebackType
from typing import (
    Any,
    Literal,
    ParamSpec,
    Protocol,
    Sequence,
    TypeAlias,
    TypeVar,
    runtime_checkable,
)
from typing_extensions import Required, TypedDict

from opentelemetry.semconv._incubating.attributes import (
    gen_ai_attributes,
    server_attributes,
)
from opentelemetry.util.types import AttributeValue

from . import _utils

P = ParamSpec("P")
ClientT = TypeVar("ClientT")
ContravariantClientT = TypeVar("ContravariantClientT", contravariant=True)
ResponseT = TypeVar("ResponseT")
CovariantResponseT = TypeVar("CovariantResponseT", covariant=True, bound=object)
StreamChunkT = TypeVar("StreamChunkT")
KwargsT = TypeVar("KwargsT", bound="BaseKwargs")
CovariantChunkT = TypeVar("CovariantChunkT", covariant=True)


class FunctionCall(TypedDict):
    """The function call parameter for a tool call parameter."""

    name: str
    """The name of the function to call."""

    arguments: str
    """The arguments of the function call as a JSON string."""


class ToolCall(TypedDict):
    """A provider-agnostic type for tool call parameters."""

    id: str
    """The ID of the tool call."""

    type: Literal["function"]
    """The discriminated union type "tool_call" for this type."""

    function: FunctionCall
    """The function call"""


class FunctionCallDeltaProtocol(Protocol):
    """The function call protocol for a tool call."""

    @property
    def name(self) -> str | None:
        """The name of the function."""
        raise NotImplementedError

    @property
    def arguments(self) -> str | None:
        """The arguments of the function call."""
        raise NotImplementedError


class ToolCallDeltaProtocol(Protocol):
    """A provider-agnostic protocol for tool calls."""

    @property
    def id(self) -> str | None:
        """The ID of the tool call."""
        raise NotImplementedError

    @property
    def type(self) -> Literal["function"] | None:
        """The type of the tool call."""
        raise NotImplementedError

    @property
    def function(self) -> FunctionCallDeltaProtocol | None:
        """The function call."""
        raise NotImplementedError

    @property
    def index(self) -> int | None:
        """The index of the tool call, if any."""
        raise NotImplementedError


@dataclass
class FunctionCallDelta:
    """The function call for a tool call."""

    name: str | None
    """The name of the function."""

    arguments: str | None
    """The arguments of the function call."""


@dataclass
class ToolCallDelta:
    """A provider-agnostic type for tool calls."""

    id: str | None
    """The ID of the tool call."""

    type: Literal["function"] | None
    """The type of the tool call."""

    function: FunctionCallDelta | None
    """The function call."""

    index: int | None
    """The index of the tool call, if any."""


@dataclass
class ChoiceDelta:
    """Represents a streaming choice delta from LLM provider response."""

    system: str
    """The LLM system identifier."""

    index: int
    """The index of this choice in the response."""

    content: str | None
    """The content delta for this streaming chunk."""

    tool_calls: Sequence[ToolCallDelta | ToolCallDeltaProtocol] | None
    """The tool call deltas if any."""

    finish_reason: str | None
    """The reason for finishing this choice, if finished."""


class Message(TypedDict, total=False):
    """A provider-agnostic type for message parameters."""

    role: Required[str]
    """The role of the message."""

    content: str
    """The content of the message."""


class BaseKwargs(TypedDict):
    """Base TypedDict for LLM provider kwargs."""


class SpanEvent(TypedDict, total=False):
    """TypedDict for OpenTelemetry span events."""

    name: Required[str]
    """The name of the span event."""

    attributes: dict[str, AttributeValue] | None
    """The attributes for the span event."""

    timestamp: int | None
    """The timestamp for the span event."""


class BoundMethod(Protocol[P, CovariantResponseT]):
    """Protocol for bound synchronous methods."""

    @property
    def __self__(self) -> object: ...

    @property
    def __name__(self) -> str: ...

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> CovariantResponseT:
        """Calls the bound method."""
        raise NotImplementedError


class BoundAsyncMethod(Protocol[P, CovariantResponseT]):
    """Protocol for bound asynchronous methods."""

    @property
    def __self__(self) -> object: ...

    @property
    def __name__(self) -> str: ...

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> CovariantResponseT:
        """Calls the bound async method."""
        raise NotImplementedError


class MethodWrapper(Protocol[P, ResponseT, ContravariantClientT]):
    """Protocol for method wrapper functions."""

    def __call__(
        self,
        wrapped: BoundMethod[P, ResponseT],
        client: ContravariantClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> ResponseT:
        """Calls the wrapper with the method and arguments."""
        raise NotImplementedError


class AsyncMethodWrapper(Protocol[P, ResponseT, ContravariantClientT]):
    """Protocol for async method wrapper functions."""

    async def __call__(
        self,
        wrapped: BoundAsyncMethod[P, ResponseT],
        client: ContravariantClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> ResponseT:
        """Calls the async wrapper with the method and arguments."""
        raise NotImplementedError


@dataclass(kw_only=True)
class GenAIRequestAttributes:
    """Dataclass for LLM request attributes used in OpenTelemetry spans."""

    GEN_AI_SYSTEM: str
    """The LLM system identifier."""

    GEN_AI_OPERATION_NAME: str = gen_ai_attributes.GenAiOperationNameValues.CHAT.value
    """The name of the LLM operation."""

    SERVER_ADDRESS: str | None = None
    """The server address for the LLM service."""

    SERVER_PORT: int | None = None
    """The server port for the LLM service."""

    GEN_AI_REQUEST_MODEL: str | None = None
    """The model name for the LLM request."""

    GEN_AI_REQUEST_TEMPERATURE: float | None = None
    """The temperature parameter for the LLM request."""

    GEN_AI_REQUEST_TOP_P: float | None = None
    """The top_p parameter for the LLM request."""

    GEN_AI_REQUEST_TOP_K: int | None = None
    """The top_k parameter for the LLM request."""

    GEN_AI_REQUEST_MAX_TOKENS: int | None = None
    """The maximum tokens for the LLM request."""

    GEN_AI_REQUEST_PRESENCE_PENALTY: float | None = None
    """The presence penalty for the LLM request."""

    GEN_AI_REQUEST_FREQUENCY_PENALTY: float | None = None
    """The frequency penalty for the LLM request."""

    GEN_AI_REQUEST_STOP_SEQUENCES: list[str] | None = None
    """The stop sequences for the LLM request."""

    GEN_AI_OPENAI_REQUEST_RESPONSE_FORMAT: str | None = None
    """The OpenAI response format for the request."""

    GEN_AI_OPENAI_REQUEST_SEED: int | None = None
    """The OpenAI seed for the request."""

    GEN_AI_OPENAI_RESPONSE_SERVICE_TIER: str | None = None
    """The OpenAI service tier for the response."""

    def dump(self) -> dict[str, AttributeValue]:
        """Returns the attributes as a dictionary suitable for OpenTelemetry spans."""
        attributes: dict[str, AttributeValue] = {}

        if self.SERVER_ADDRESS:
            attributes[server_attributes.SERVER_ADDRESS] = self.SERVER_ADDRESS
        if self.SERVER_PORT and self.SERVER_PORT > 0 and self.SERVER_PORT != 443:
            attributes[server_attributes.SERVER_PORT] = (
                self.SERVER_PORT
            )  # pragma: no cover

        for field in fields(self):
            if field.name in ["SERVER_ADDRESS", "SERVER_PORT"]:
                continue
            value = getattr(self, field.name)
            if value is None:
                continue
            attributes[getattr(gen_ai_attributes, field.name)] = value

        return attributes


@dataclass(kw_only=True)
class GenAIResponseAttributes:
    """Dataclass for LLM response attributes used in OpenTelemetry spans."""

    GEN_AI_RESPONSE_ID: str | None = None
    """The unique identifier for the LLM response."""

    GEN_AI_RESPONSE_MODEL: str | None = None
    """The model used for the LLM response."""

    GEN_AI_RESPONSE_FINISH_REASONS: list[str] | None = None
    """The finish reasons for the LLM response choices."""

    GEN_AI_OPENAI_REQUEST_SERVICE_TIER: str | None = None
    """The OpenAI service tier for the request."""

    GEN_AI_USAGE_INPUT_TOKENS: int | None = None
    """The number of input tokens used in the LLM request."""

    GEN_AI_USAGE_OUTPUT_TOKENS: int | None = None
    """The number of output tokens generated by the LLM."""

    def dump(self) -> dict[str, AttributeValue]:
        """Returns the attributes as a dictionary suitable for OpenTelemetry spans."""
        return {
            getattr(gen_ai_attributes, field.name): value
            for field in fields(self)
            if (value := getattr(self, field.name)) is not None
        }

    def update(self, attributes: "GenAIResponseAttributes") -> None:
        """Updates this instance with non-null values from another `GenAIResponseAttributes`."""
        for field in fields(attributes):
            if not getattr(self, field.name):
                setattr(self, field.name, getattr(attributes, field.name))


@dataclass(kw_only=True)
class ChoiceEvent:
    """Represents a choice event from LLM response for OpenTelemetry spans."""

    system: str
    """The LLM system identifier."""

    index: int
    """The index of this choice in the response."""

    message: Message
    """The message content for this choice."""

    finish_reason: str | None = None
    """The reason for finishing this choice."""

    tool_calls: list[ToolCall] | None = None
    """The tool calls made in this choice."""

    timestamp: int | None = None
    """The timestamp for this choice event."""

    def dump(self) -> SpanEvent:
        """Returns the choice event as a span event for OpenTelemetry."""
        attributes: dict[str, AttributeValue] = {
            gen_ai_attributes.GEN_AI_SYSTEM: self.system
        }
        for field in fields(self):
            if field.name == "system":
                continue
            value = _utils.serialize_attribute_value(getattr(self, field.name))
            if value is None:
                continue
            attributes[field.name] = value

        return {
            "name": "gen_ai.choice",
            "attributes": attributes,
            "timestamp": self.timestamp,
        }


@dataclass(kw_only=True)
class BaseMessageEvent(ABC):
    """Abstract base class for LLM message events in OpenTelemetry spans."""

    @property
    @abstractmethod
    def role(self) -> str:
        """Returns the role of this message event."""
        ...

    system: str
    """The LLM system identifier."""

    timestamp: int | None = None
    """The timestamp for this message event."""

    def dump(self) -> SpanEvent:
        """Returns the message event as a span event for OpenTelemetry."""
        attributes: dict[str, AttributeValue] = {
            gen_ai_attributes.GEN_AI_SYSTEM: self.system,
        }
        for field in fields(self):
            if field.name == "system":
                continue
            value = _utils.serialize_attribute_value(getattr(self, field.name))
            if value is None:
                continue
            attributes[field.name] = value

        return {
            "name": f"gen_ai.{self.role}.message",
            "attributes": attributes,
            "timestamp": self.timestamp,
        }


@dataclass(kw_only=True)
class SystemMessageEvent(BaseMessageEvent):
    """Represents a system message event for OpenTelemetry spans."""

    @property
    def role(self) -> Literal["system"]:
        """Returns 'system' as the role for this message event."""
        return "system"

    content: Any | None = None
    """The content of the system message."""


@dataclass(kw_only=True)
class UserMessageEvent(BaseMessageEvent):
    """Represents a user message event for OpenTelemetry spans."""

    @property
    def role(self) -> Literal["user"]:
        """Returns 'user' as the role for this message event."""
        return "user"

    content: Any | None = None
    """The content of the user message."""


@dataclass(kw_only=True)
class AssistantMessageEvent(BaseMessageEvent):
    """Represents an assistant message event for OpenTelemetry spans."""

    @property
    def role(self) -> Literal["assistant"]:
        """Returns 'assistant' as the role for this message event."""
        return "assistant"

    content: Any | None = None
    """The content of the assistant message."""

    tool_calls: list[ToolCall] | None = None
    """The tool calls made by the assistant."""


@dataclass(kw_only=True)
class ToolMessageEvent(BaseMessageEvent):
    """Represents a tool message event for OpenTelemetry spans."""

    @property
    def role(self) -> Literal["tool"]:
        """Returns 'tool' as the role for this message event."""
        return "tool"

    content: Any | None = None
    """The content of the tool message."""

    id: str | None = None
    """The identifier for the tool call."""


MessageEvent: TypeAlias = (
    SystemMessageEvent | UserMessageEvent | AssistantMessageEvent | ToolMessageEvent
)


@runtime_checkable
class Stream(Protocol[CovariantChunkT]):
    """Protocol for synchronous stream objects."""

    def __iter__(self) -> Iterator[CovariantChunkT]:
        """Returns an iterator for the stream."""
        raise NotImplementedError

    def __next__(self) -> CovariantChunkT:
        """Get the next item from the stream."""
        raise NotImplementedError

    def close(self) -> None:
        """Close the stream and release resources."""
        raise NotImplementedError


@runtime_checkable
class StreamContextManager(Protocol[CovariantChunkT]):
    """Protocol for context manager objects that yield synchronous stream objects."""

    def __enter__(self) -> Stream[CovariantChunkT]:
        """Enter the context and return a stream."""
        raise NotImplementedError

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        """Exit the context and clean up resources."""
        raise NotImplementedError


@runtime_checkable
class AsyncStream(Protocol[CovariantChunkT]):
    """Protocol for asynchronous stream objects."""

    def __aiter__(self) -> AsyncIterator[CovariantChunkT]:
        """Returns an async iterator for the stream."""
        raise NotImplementedError

    async def __anext__(self) -> CovariantChunkT:
        """Get the next item from the async stream."""
        raise NotImplementedError

    async def close(self) -> None:
        """Close the async stream and release resources."""
        raise NotImplementedError


@runtime_checkable
class AsyncStreamContextManager(Protocol[CovariantChunkT]):
    """Protocol for async context manager objects that yield asynchronous stream objects."""

    async def __aenter__(self) -> AsyncStream[CovariantChunkT]:
        """Enter the async context and return an async stream."""
        raise NotImplementedError

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        """Exit the async context and clean up resources."""
        raise NotImplementedError
