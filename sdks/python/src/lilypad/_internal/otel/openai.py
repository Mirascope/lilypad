"""The `OpenAIInstrumentor` implementation for instrumenting OpenAI clients."""

from typing import Iterable, Literal, TypeAlias, cast
from typing_extensions import Required

from openai import AsyncAzureOpenAI, AsyncOpenAI, AzureOpenAI, OpenAI
from openai.types import ChatModel
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionAudioParam,
    ChatCompletionChunk,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCall,
    ChatCompletionMessageToolCallParam,
    ChatCompletionPredictionContentParam,
    ChatCompletionStreamOptionsParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
    ParsedChatCompletion,
)
from openai.types.chat.completion_create_params import (
    Function,
    FunctionCall,
    ResponseFormat,
    WebSearchOptions,
)
from openai.types.shared_params import Metadata, ReasoningEffort
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from . import _utils
from .base_instrumentor import BaseInstrumentor
from .types import (
    AssistantMessageEvent,
    BaseKwargs,
    ChoiceDelta,
    ChoiceEvent,
    GenAIRequestAttributes,
    GenAIResponseAttributes,
    Message,
    MessageEvent,
    SystemMessageEvent,
    ToolMessageEvent,
    UserMessageEvent,
)

OPENAI_SYSTEM = gen_ai_attributes.GenAiSystemValues.OPENAI.value

OpenAIClient: TypeAlias = OpenAI | AsyncOpenAI | AsyncAzureOpenAI | AzureOpenAI


class OpenAIKwargs(BaseKwargs, total=False):
    """TypedDict for OpenAI chat completion parameters."""

    # REQUIRED
    messages: Required[Iterable[ChatCompletionMessageParam]]
    model: Required[ChatModel | str]

    # NOT REQUIRED
    audio: ChatCompletionAudioParam | None
    frequency_penalty: float | None
    function_call: FunctionCall | None
    functions: Iterable[Function] | None
    logit_bias: dict[str, int] | None
    logprobs: bool | None
    max_completion_tokens: int | None
    max_tokens: int | None
    metadata: Metadata | None
    modalities: list[Literal["text", "audio"]] | None
    n: int | None
    parallel_tool_calls: bool | None
    prediction: ChatCompletionPredictionContentParam | None
    presence_penalty: float | None
    prompt_cache_key: str | None
    reasoning_effort: ReasoningEffort | None
    response_format: ResponseFormat | None
    safety_identifier: str | None
    seed: int | None
    service_tier: Literal["auto", "default", "flex", "scale", "priority"] | None
    stop: str | list[str] | None
    store: bool | None
    stream: bool | None
    stream_options: ChatCompletionStreamOptionsParam | None
    temperature: float | None
    tool_choice: ChatCompletionToolChoiceOptionParam | None
    tools: Iterable[ChatCompletionToolParam] | None
    top_logprobs: int | None
    top_p: float | None
    user: str | None
    web_search_options: WebSearchOptions | None


def _get_tool_call_params(
    message: ChatCompletionMessage | ChatCompletionAssistantMessageParam,
) -> list[ChatCompletionMessageToolCallParam]:
    """Returns tool calls extracted from a message object or dictionary."""
    if isinstance(message, dict):
        tool_calls = message.get("tool_calls")
    else:
        tool_calls = message.tool_calls

    return [
        ChatCompletionMessageToolCallParam(
            id=tool_call.id,
            type=tool_call.type,
            function={
                "name": tool_call.function.name,
                "arguments": tool_call.function.arguments,
            },
        )
        if isinstance(tool_call, ChatCompletionMessageToolCall)
        else tool_call
        for tool_call in tool_calls or []
    ]


class _OpenAIInstrumentor(
    BaseInstrumentor[
        OpenAIClient,
        OpenAIKwargs,
        ChatCompletion | ParsedChatCompletion,
        ChatCompletionChunk,
    ]
):
    """[MISSING DOCSTRING]"""

    @staticmethod
    def _get_request_attributes(
        kwargs: OpenAIKwargs,
        client: OpenAIClient,
    ) -> GenAIRequestAttributes:
        """[MISSING DOCSTRING]"""
        stop_sequences = kwargs.get("stop")
        if isinstance(stop_sequences, str):
            stop_sequences = [stop_sequences]
        response_format = kwargs.get("response_format")
        if response_format:
            response_format = (
                response_format.get("type")
                if isinstance(response_format, dict)
                else response_format.__name__
            )
        service_tier = kwargs.get("service_tier")
        if service_tier == "auto":
            service_tier = None
        return GenAIRequestAttributes(
            GEN_AI_SYSTEM=OPENAI_SYSTEM,
            SERVER_ADDRESS=client._client.base_url.host,
            SERVER_PORT=client._client.base_url.port,
            GEN_AI_REQUEST_MODEL=kwargs.get("model"),
            GEN_AI_REQUEST_TEMPERATURE=kwargs.get("temperature"),
            GEN_AI_REQUEST_TOP_P=kwargs.get("top_p"),
            GEN_AI_REQUEST_MAX_TOKENS=kwargs.get("max_tokens"),
            GEN_AI_REQUEST_PRESENCE_PENALTY=kwargs.get("presence_penalty"),
            GEN_AI_REQUEST_FREQUENCY_PENALTY=kwargs.get("frequency_penalty"),
            GEN_AI_REQUEST_STOP_SEQUENCES=stop_sequences,
            GEN_AI_OPENAI_REQUEST_RESPONSE_FORMAT=response_format,
            GEN_AI_OPENAI_REQUEST_SEED=kwargs.get("seed"),
            GEN_AI_OPENAI_RESPONSE_SERVICE_TIER=service_tier,
        )

    @staticmethod
    def _process_messages(
        kwargs: OpenAIKwargs,
    ) -> list[MessageEvent]:
        """[MISSING DOCSTRING]"""
        message_events: list[MessageEvent] = []
        for message in kwargs.get("messages", []):
            match message["role"]:
                case "system":
                    message_events.append(
                        SystemMessageEvent(
                            system=OPENAI_SYSTEM,
                            content=message["content"],
                        )
                    )
                case "user":
                    message_events.append(
                        UserMessageEvent(
                            system=OPENAI_SYSTEM,
                            content=message["content"],
                        )
                    )
                case "assistant":
                    message_events.append(
                        AssistantMessageEvent(
                            system=OPENAI_SYSTEM,
                            content=message.get("content"),
                            tool_calls=_get_tool_call_params(message) or None,
                        )
                    )
                case "tool":
                    message_events.append(
                        ToolMessageEvent(
                            system=OPENAI_SYSTEM,
                            content=message["content"],
                            id=message["tool_call_id"],
                        )
                    )

        return message_events

    @staticmethod
    def _process_response(
        response: ChatCompletion | ParsedChatCompletion,
    ) -> tuple[list[ChoiceEvent], GenAIResponseAttributes]:
        """[MISSING DOCSTRING]"""
        choice_events: list[ChoiceEvent] = []
        finish_reasons: list[str] = []
        for choice in response.choices:
            finish_reasons.append(choice.finish_reason)
            choice_events.append(
                ChoiceEvent(
                    system=OPENAI_SYSTEM,
                    index=choice.index,
                    message=cast(
                        Message,
                        choice.message.model_dump(include={"role", "content"}),
                    ),
                    finish_reason=choice.finish_reason,
                    tool_calls=_get_tool_call_params(choice.message) or None,
                )
            )

        input_tokens, output_tokens = None, None
        if response.usage:
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
        response_attributes = GenAIResponseAttributes(
            GEN_AI_RESPONSE_ID=response.id,
            GEN_AI_RESPONSE_MODEL=response.model,
            GEN_AI_RESPONSE_FINISH_REASONS=finish_reasons or None,
            GEN_AI_OPENAI_REQUEST_SERVICE_TIER=response.service_tier,
            GEN_AI_USAGE_INPUT_TOKENS=input_tokens,
            GEN_AI_USAGE_OUTPUT_TOKENS=output_tokens,
        )

        return choice_events, response_attributes

    @staticmethod
    def _process_chunk(
        chunk: ChatCompletionChunk,
    ) -> tuple[GenAIResponseAttributes, list[ChoiceDelta]]:
        """[MISSING DOCSTRING]"""
        response_attributes = GenAIResponseAttributes()
        choice_deltas: list[ChoiceDelta] = []
        response_attributes.GEN_AI_RESPONSE_ID = chunk.id
        response_attributes.GEN_AI_RESPONSE_MODEL = chunk.model
        response_attributes.GEN_AI_OPENAI_REQUEST_SERVICE_TIER = chunk.service_tier
        if chunk.usage:
            response_attributes.GEN_AI_USAGE_INPUT_TOKENS = chunk.usage.prompt_tokens
            response_attributes.GEN_AI_USAGE_OUTPUT_TOKENS = (
                chunk.usage.completion_tokens
            )

        finish_reasons = []
        for choice in chunk.choices:
            if choice.finish_reason:
                finish_reasons.append(choice.finish_reason)
            choice_deltas.append(
                ChoiceDelta(
                    system=OPENAI_SYSTEM,
                    index=choice.index,
                    content=choice.delta.content,
                    tool_calls=choice.delta.tool_calls,
                    finish_reason=choice.finish_reason,
                )
            )

        response_attributes.GEN_AI_RESPONSE_FINISH_REASONS = finish_reasons

        return response_attributes, choice_deltas


def instrument_openai(
    client: OpenAIClient,
) -> None:
    """[MISSING DOCSTRING]"""
    if _utils.client_is_already_instrumented(client):
        return

    instrumentor = _OpenAIInstrumentor()

    if isinstance(client, OpenAI | AzureOpenAI):
        instrumentor.instrument_generate(client.chat.completions.create)
        instrumentor.instrument_generate(client.chat.completions.parse)
        # NOTE: we don't actually need to instrument `.stream` as it uses `.create` with
        # `stream=True` under the hood, which we've already instrumented
        # instrumentor.instrument_generate(client.chat.completions.stream)
    else:
        instrumentor.instrument_async_generate(client.chat.completions.create)
        instrumentor.instrument_async_generate(client.chat.completions.parse)
        # NOTE: we don't actually need to instrument `.stream` as it uses `.create` with
        # `stream=True` under the hood, which we've already instrumented
        # instrumentor.instrument_generate(client.chat.completions.stream)

    _utils.mark_client_as_instrumented(client)
