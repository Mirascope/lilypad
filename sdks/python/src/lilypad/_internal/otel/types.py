"""Types for OpenTelemetry provider-agnostic LLM handling."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from typing import (
    Any,
    Literal,
    ParamSpec,
    Protocol,
    Sequence,
    TypeAlias,
    TypeVar,
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
    """[MISSING DOCSTRING]"""

    system: str
    """[MISSING DOCSTRING]"""

    index: int
    """[MISSING DOCSTRING]"""

    content: str | None
    """[MISSING DOCSTRING]"""

    tool_calls: Sequence[ToolCallDelta | ToolCallDeltaProtocol] | None
    """[MISSING DOCSTRING]"""

    finish_reason: str | None
    """[MISSING DOCSTRING]"""


class Message(TypedDict, total=False):
    """A provider-agnostic type for message parameters."""

    role: Required[str]
    """The role of the message."""

    content: str
    """The content of the message."""


class BaseKwargs(TypedDict):
    """[MISSING DOCSTRING]"""


class SpanEvent(TypedDict, total=False):
    """[MISSING DOCSTRING]"""

    name: Required[str]
    """[MISSING DOCSTRING]"""

    attributes: dict[str, AttributeValue] | None
    """[MISSING DOCSTRING]"""

    timestamp: int | None
    """[MISSING DOCSTRING]"""


class BoundMethod(Protocol[P, CovariantResponseT]):
    """[MISSING DOCSTRING]"""

    @property
    def __self__(self) -> object: ...

    @property
    def __name__(self) -> str: ...

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> CovariantResponseT:
        """[MISSING DOCSTRING]"""
        raise NotImplementedError


class BoundAsyncMethod(Protocol[P, CovariantResponseT]):
    """[MISSING DOCSTRING]"""

    @property
    def __self__(self) -> object: ...

    @property
    def __name__(self) -> str: ...

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> CovariantResponseT:
        """[MISSING DOCSTRING]"""
        raise NotImplementedError


class MethodWrapper(Protocol[P, ResponseT, ContravariantClientT]):
    """[MISSING DOCSTRING]"""

    def __call__(
        self,
        wrapped: BoundMethod[P, ResponseT],
        client: ContravariantClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> ResponseT:
        """[MISSING DOCSTRING]"""
        raise NotImplementedError


class AsyncMethodWrapper(Protocol[P, ResponseT, ContravariantClientT]):
    """[MISSING DOCSTRING]"""

    async def __call__(
        self,
        wrapped: BoundAsyncMethod[P, ResponseT],
        client: ContravariantClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> ResponseT:
        """[MISSING DOCSTRING]"""
        raise NotImplementedError


@dataclass(kw_only=True)
class GenAIRequestAttributes:
    """[MISSING DOCSTRING]"""

    GEN_AI_SYSTEM: str
    """[MISSING DOCSTRING]"""

    GEN_AI_OPERATION_NAME: str = gen_ai_attributes.GenAiOperationNameValues.CHAT.value
    """[MISSING DOCSTRING]"""

    SERVER_ADDRESS: str | None = None
    """[MISSING DOCSTRING]"""

    SERVER_PORT: int | None = None
    """[MISSING DOCSTRING]"""

    GEN_AI_REQUEST_MODEL: str | None = None
    """[MISSING DOCSTRING]"""

    GEN_AI_REQUEST_TEMPERATURE: float | None = None
    """[MISSING DOCSTRING]"""

    GEN_AI_REQUEST_TOP_P: float | None = None
    """[MISSING DOCSTRING]"""

    GEN_AI_REQUEST_TOP_K: int | None = None
    """[MISSING DOCSTRING]"""

    GEN_AI_REQUEST_MAX_TOKENS: int | None = None
    """[MISSING DOCSTRING]"""

    GEN_AI_REQUEST_PRESENCE_PENALTY: float | None = None
    """[MISSING DOCSTRING]"""

    GEN_AI_REQUEST_FREQUENCY_PENALTY: float | None = None
    """[MISSING DOCSTRING]"""

    GEN_AI_REQUEST_STOP_SEQUENCES: list[str] | None = None
    """[MISSING DOCSTRING]"""

    GEN_AI_OPENAI_REQUEST_RESPONSE_FORMAT: str | None = None
    """[MISSING DOCSTRING]"""

    GEN_AI_OPENAI_REQUEST_SEED: int | None = None
    """[MISSING DOCSTRING]"""

    GEN_AI_OPENAI_RESPONSE_SERVICE_TIER: str | None = None
    """[MISSING DOCSTRING]"""

    def dump(self) -> dict[str, AttributeValue]:
        """[MISSING DOCSTRING]"""
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
    """[MISSING DOCSTRING]"""

    GEN_AI_RESPONSE_ID: str | None = None
    """[MISSING DOCSTRING]"""

    GEN_AI_RESPONSE_MODEL: str | None = None
    """[MISSING DOCSTRING]"""

    GEN_AI_RESPONSE_FINISH_REASONS: list[str] | None = None
    """[MISSING DOCSTRING]"""

    GEN_AI_OPENAI_REQUEST_SERVICE_TIER: str | None = None
    """[MISSING DOCSTRING]"""

    GEN_AI_USAGE_INPUT_TOKENS: int | None = None
    """[MISSING DOCSTRING]"""

    GEN_AI_USAGE_OUTPUT_TOKENS: int | None = None
    """[MISSING DOCSTRING]"""

    def dump(self) -> dict[str, AttributeValue]:
        """[MISSING DOCSTRING]"""
        return {
            getattr(gen_ai_attributes, field.name): value
            for field in fields(self)
            if (value := getattr(self, field.name)) is not None
        }

    def update(self, attributes: "GenAIResponseAttributes") -> None:
        """[MISSING DOCSTRING]"""
        for field in fields(attributes):
            if not getattr(self, field.name):
                setattr(self, field.name, getattr(attributes, field.name))


@dataclass(kw_only=True)
class ChoiceEvent:
    """[MISSING DOCSTRING]"""

    system: str
    """[MISSING DOCSTRING]"""

    index: int
    """[MISSING DOCSTRING]"""

    message: Message
    """[MISSING DOCSTRING]"""

    finish_reason: str | None = None
    """[MISSING DOCSTRING]"""

    tool_calls: list[ToolCall] | None = None
    """[MISSING DOCSTRING]"""

    timestamp: int | None = None
    """[MISSING DOCSTRING]"""

    def dump(self) -> SpanEvent:
        """[MISSING DOCSTRING]"""
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
    """[MISSING DOCSTRING]"""

    @property
    @abstractmethod
    def role(self) -> str:
        """[MISSING DOCSTRING]"""
        ...

    system: str
    """[MISSING DOCSTRING]"""

    timestamp: int | None = None
    """[MISSING DOCSTRING]"""

    def dump(self) -> SpanEvent:
        """[MISSING DOCSTRING]"""
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
    """[MISSING DOCSTRING]"""

    @property
    def role(self) -> Literal["system"]:
        """[MISSING DOCSTRING]"""
        return "system"

    content: Any | None = None
    """[MISSING DOCSTRING]"""


@dataclass(kw_only=True)
class UserMessageEvent(BaseMessageEvent):
    """[MISSING DOCSTRING]"""

    @property
    def role(self) -> Literal["user"]:
        """[MISSING DOCSTRING]"""
        return "user"

    content: Any | None = None
    """[MISSING DOCSTRING]"""


@dataclass(kw_only=True)
class AssistantMessageEvent(BaseMessageEvent):
    """[MISSING DOCSTRING]"""

    @property
    def role(self) -> Literal["assistant"]:
        """[MISSING DOCSTRING]"""
        return "assistant"

    content: Any | None = None
    """[MISSING DOCSTRING]"""

    tool_calls: list[ToolCall] | None = None
    """[MISSING DOCSTRING]"""


@dataclass(kw_only=True)
class ToolMessageEvent(BaseMessageEvent):
    """[MISSING DOCSTRING]"""

    @property
    def role(self) -> Literal["tool"]:
        """[MISSING DOCSTRING]"""
        return "tool"

    content: Any | None = None
    """[MISSING DOCSTRING]"""

    id: str | None = None
    """[MISSING DOCSTRING]"""


MessageEvent: TypeAlias = (
    SystemMessageEvent | UserMessageEvent | AssistantMessageEvent | ToolMessageEvent
)
