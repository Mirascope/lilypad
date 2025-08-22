"""The `AnthropicInstrumentor` implementation for instrumenting Anthropic clients."""

import logging
from typing import Iterable, Literal, TypeAlias, cast
from typing_extensions import Required

from anthropic import (
    Anthropic,
    AnthropicBedrock,
    AnthropicVertex,
    AsyncAnthropic,
    AsyncAnthropicBedrock,
    AsyncAnthropicVertex,
)
from anthropic.types import (
    Message as AnthropicMessage,
    MessageParam,
    MessageStreamEvent,
    MetadataParam,
    ModelParam,
    TextBlockParam,
    ThinkingConfigParam,
    ToolChoiceParam,
    ToolUnionParam,
)
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from lilypad._internal.utils import json_dumps

from . import _utils
from .base_instrumentor import BaseInstrumentor
from .types import (
    AssistantMessageEvent,
    BaseKwargs,
    ChoiceDelta,
    ChoiceEvent,
    FunctionCall,
    FunctionCallDelta,
    GenAIRequestAttributes,
    GenAIResponseAttributes,
    Message,
    MessageEvent,
    SystemMessageEvent,
    ToolCall,
    ToolCallDelta,
    ToolMessageEvent,
    UserMessageEvent,
)

logger = logging.getLogger(__name__)


_ANTHROPIC_SYSTEM = gen_ai_attributes.GenAiSystemValues.ANTHROPIC.value

AnthropicClient: TypeAlias = (
    Anthropic
    | AnthropicBedrock
    | AnthropicVertex
    | AsyncAnthropic
    | AsyncAnthropicBedrock
    | AsyncAnthropicVertex
)


class _AnthropicKwargs(BaseKwargs, total=False):
    """TypedDict for Anthropic message creation parameters."""

    # REQUIRED
    max_tokens: Required[int]
    messages: Required[Iterable[MessageParam]]
    model: Required[ModelParam]

    # NOT REQUIRED
    metadata: MetadataParam
    service_tier: Literal["auto", "standard_only"]
    stop_sequences: list[str]
    stream: bool
    system: str | Iterable[TextBlockParam]
    temperature: float
    thinking: ThinkingConfigParam
    tool_choice: ToolChoiceParam
    tools: Iterable[ToolUnionParam]
    top_k: int
    top_p: float


def _process_user_message(
    message: MessageParam,
) -> tuple[UserMessageEvent, list[ToolMessageEvent]]:
    """Returns user message event and any tool message events from Anthropic message."""
    content = message["content"]
    if isinstance(content, str):
        return UserMessageEvent(system=_ANTHROPIC_SYSTEM, content=content), []
    text, tool_message_events = "", []
    for block in content:
        if not isinstance(block, dict):
            if block.type == "text":
                text += block.text
        else:
            if block["type"] == "text":
                text += block["text"]
            elif block["type"] == "tool_result":
                tool_message_events.append(
                    ToolMessageEvent(
                        system=_ANTHROPIC_SYSTEM,
                        content=block.get("content"),
                        id=block.get("tool_use_id"),
                    )
                )
    user_message_event = UserMessageEvent(
        system=_ANTHROPIC_SYSTEM, content=text or None
    )
    return user_message_event, tool_message_events


def _process_assistant_message(
    message: MessageParam | AnthropicMessage,
) -> tuple[str, list[ToolCall]]:
    """Returns content string and tool calls from Anthropic assistant message."""
    if isinstance(message, AnthropicMessage):
        message = cast(MessageParam, message.model_dump())
    content = message["content"]
    if isinstance(content, str):
        return content, []
    text, tool_calls = "", []
    for block in content:
        if not isinstance(block, dict):
            if block.type == "text":
                text += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        type="function",
                        function=FunctionCall(
                            name=block.name,
                            arguments=json_dumps(block.input),
                        ),
                    )
                )
        else:
            if block["type"] == "text":
                text += block["text"]
            elif block["type"] == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block["id"],
                        type="function",
                        function=FunctionCall(
                            name=block["name"],
                            arguments=json_dumps(block["input"]),
                        ),
                    )
                )
    return text, tool_calls


class _AnthropicInstrumentor(
    BaseInstrumentor[
        AnthropicClient,
        _AnthropicKwargs,
        AnthropicMessage,
        MessageStreamEvent,
    ]
):
    """Anthropic client instrumentor for telemetry and tracing."""

    @staticmethod
    def _get_request_attributes(
        kwargs: _AnthropicKwargs,
        client: AnthropicClient,
    ) -> GenAIRequestAttributes:
        """Returns request attributes extracted from Anthropic message kwargs."""
        return GenAIRequestAttributes(
            GEN_AI_SYSTEM=_ANTHROPIC_SYSTEM,
            SERVER_ADDRESS=client._client.base_url.host,
            SERVER_PORT=client._client.base_url.port,
            GEN_AI_REQUEST_MODEL=kwargs.get("model"),
            GEN_AI_REQUEST_TEMPERATURE=kwargs.get("temperature"),
            GEN_AI_REQUEST_TOP_P=kwargs.get("top_p"),
            GEN_AI_REQUEST_TOP_K=kwargs.get("top_k"),
            GEN_AI_REQUEST_MAX_TOKENS=kwargs.get("max_tokens"),
            GEN_AI_REQUEST_STOP_SEQUENCES=kwargs.get("stop_sequences"),
        )

    @staticmethod
    def _process_messages(
        kwargs: _AnthropicKwargs,
    ) -> list[MessageEvent]:
        """Returns standardized message events converted from Anthropic messages."""
        message_events: list[MessageEvent] = []
        if system_content := kwargs.get("system"):
            message_events.append(
                SystemMessageEvent(system=_ANTHROPIC_SYSTEM, content=system_content)
            )
        for message in kwargs.get("messages", []):
            match message["role"]:
                case "user":
                    user_message_event, tool_message_events = _process_user_message(
                        message
                    )
                    message_events.append(user_message_event)
                    message_events += tool_message_events
                case "assistant":
                    content, tool_calls = _process_assistant_message(message)
                    message_events.append(
                        AssistantMessageEvent(
                            system=_ANTHROPIC_SYSTEM,
                            content=content,
                            tool_calls=tool_calls or None,
                        )
                    )

        return message_events

    @staticmethod
    def _process_response(
        response: AnthropicMessage,
    ) -> tuple[list[ChoiceEvent], GenAIResponseAttributes]:
        """Returns the choice events list and response attributes from Anthropic response."""
        content, tool_calls = _process_assistant_message(response)
        choice_event = ChoiceEvent(
            system=_ANTHROPIC_SYSTEM,
            index=0,
            message=Message(role="assistant", content=content),
            finish_reason=response.stop_reason,
            tool_calls=tool_calls or None,
        )

        finish_reasons = [response.stop_reason] if response.stop_reason else None
        response_attributes = GenAIResponseAttributes(
            GEN_AI_RESPONSE_ID=response.id,
            GEN_AI_RESPONSE_MODEL=response.model,
            GEN_AI_RESPONSE_FINISH_REASONS=finish_reasons,
            GEN_AI_USAGE_INPUT_TOKENS=response.usage.input_tokens,
            GEN_AI_USAGE_OUTPUT_TOKENS=response.usage.output_tokens,
        )

        return [choice_event], response_attributes

    @staticmethod
    def _process_chunk(
        chunk: MessageStreamEvent,
    ) -> tuple[GenAIResponseAttributes, list[ChoiceDelta]]:
        """Returns response attributes and choice deltas from Anthropic streaming chunk."""
        response_attributes = GenAIResponseAttributes()
        choice_delta = ChoiceDelta(
            system=_ANTHROPIC_SYSTEM,
            index=0,
            content=None,
            tool_calls=None,
            finish_reason=None,
        )

        if chunk.type == "message_start":
            response_attributes.GEN_AI_RESPONSE_ID = chunk.message.id
            response_attributes.GEN_AI_RESPONSE_MODEL = chunk.message.model
        elif chunk.type == "message_delta":
            if chunk.delta.stop_reason:
                response_attributes.GEN_AI_RESPONSE_FINISH_REASONS = [
                    chunk.delta.stop_reason
                ]
                choice_delta.finish_reason = chunk.delta.stop_reason
            if chunk.usage.input_tokens is not None:
                response_attributes.GEN_AI_USAGE_INPUT_TOKENS = chunk.usage.input_tokens
            if chunk.usage.output_tokens is not None:
                response_attributes.GEN_AI_USAGE_OUTPUT_TOKENS = (
                    chunk.usage.output_tokens
                )
        elif chunk.type == "content_block_start":
            if chunk.content_block.type == "tool_use":
                choice_delta.tool_calls = [
                    ToolCallDelta(
                        id=chunk.content_block.id,
                        type="function",
                        function=FunctionCallDelta(
                            name=chunk.content_block.name, arguments=None
                        ),
                        index=chunk.index,
                    )
                ]
        elif chunk.type == "content_block_delta":
            if chunk.delta.type == "text_delta":
                choice_delta.content = chunk.delta.text
            elif chunk.delta.type == "input_json_delta":
                choice_delta.tool_calls = [
                    ToolCallDelta(
                        id=None,
                        type="function",
                        function=FunctionCallDelta(
                            name=None,
                            arguments=json_dumps(chunk.delta.partial_json),
                        ),
                        index=chunk.index,
                    )
                ]

        return response_attributes, [choice_delta]


def instrument_anthropic(
    client: AnthropicClient,
) -> None:
    """Instruments an Anthropic client for telemetry collection."""
    if _utils.client_is_already_instrumented(client):
        return

    instrumentor = _AnthropicInstrumentor()

    if isinstance(client, Anthropic | AnthropicBedrock | AnthropicVertex):
        instrumentor.instrument_generate(client.messages.create)
        instrumentor.instrument_generate(client.messages.stream)
    else:
        instrumentor.instrument_async_generate(client.messages.create)
        # NOTE: this method is not awaitable, so we use the sync path for async context managers
        instrumentor.instrument_generate(client.messages.stream)

    _utils.mark_client_as_instrumented(client)
