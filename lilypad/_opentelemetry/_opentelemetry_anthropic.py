"""OpenTelemetry Anthropic instrumentation"""

import contextlib
import json
import logging
import os
import time
from collections.abc import Callable, Collection, Coroutine
from typing import Any

from anthropic._streaming import AsyncStream, Stream
from opentelemetry import context as context_api
from opentelemetry.context import _SUPPRESS_INSTRUMENTATION_KEY
from opentelemetry.instrumentation.anthropic.streaming import (
    abuild_from_streaming_response,
    build_from_streaming_response,
)
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.utils import unwrap
from opentelemetry.metrics import Counter, Histogram, Meter, get_meter
from opentelemetry.semconv_ai import (
    SUPPRESS_LANGUAGE_MODEL_INSTRUMENTATION_KEY,
    LLMRequestTypeValues,
    Meters,
    SpanAttributes,
)
from opentelemetry.trace import SpanKind, Tracer, get_tracer
from opentelemetry.trace.status import Status, StatusCode
from wrapt import wrap_function_wrapper

from ._utils import (
    Method,
    _set_span_attribute,
    dont_throw,
    run_async,
)

logger = logging.getLogger(__name__)

_instruments = ("anthropic >= 0.3.11",)

WRAPPED_METHODS: list[Method] = [
    {
        "package": "anthropic.resources.completions",
        "object": "Completions",
        "method": "create",
        "span_name": "anthropic.completion",
    },
    {
        "package": "anthropic.resources.messages",
        "object": "Messages",
        "method": "create",
        "span_name": "anthropic.chat",
    },
    {
        "package": "anthropic.resources.messages",
        "object": "Messages",
        "method": "stream",
        "span_name": "anthropic.chat",
    },
    {
        "package": "anthropic.resources.beta.prompt_caching.messages",
        "object": "Messages",
        "method": "create",
        "span_name": "anthropic.chat",
    },
    {
        "package": "anthropic.resources.beta.prompt_caching.messages",
        "object": "Messages",
        "method": "stream",
        "span_name": "anthropic.chat",
    },
]

WRAPPED_AMETHODS: list[Method] = [
    {
        "package": "anthropic.resources.completions",
        "object": "AsyncCompletions",
        "method": "create",
        "span_name": "anthropic.completion",
    },
    {
        "package": "anthropic.resources.messages",
        "object": "AsyncMessages",
        "method": "create",
        "span_name": "anthropic.chat",
    },
    {
        "package": "anthropic.resources.messages",
        "object": "AsyncMessages",
        "method": "stream",
        "span_name": "anthropic.chat",
    },
    {
        "package": "anthropic.resources.beta.prompt_caching.messages",
        "object": "AsyncMessages",
        "method": "create",
        "span_name": "anthropic.chat",
    },
    {
        "package": "anthropic.resources.beta.prompt_caching.messages",
        "object": "AsyncMessages",
        "method": "stream",
        "span_name": "anthropic.chat",
    },
]


@dont_throw
def error_metrics_attributes(exception: Exception) -> dict[str, Any]:
    return {
        SpanAttributes.LLM_SYSTEM: "anthropic",
        "error.type": exception.__class__.__name__,
    }


@dont_throw
def shared_metrics_attributes(response: dict | object) -> dict[str, Any]:
    if not isinstance(response, dict):
        response = response.__dict__

    return {
        SpanAttributes.LLM_SYSTEM: "anthropic",
        SpanAttributes.LLM_RESPONSE_MODEL: response.get("model"),
    }


@dont_throw
def count_prompt_tokens_from_request(anthropic, request):
    prompt_tokens = 0
    if hasattr(anthropic, "count_tokens"):
        if request.get("prompt"):
            prompt_tokens = anthropic.count_tokens(request.get("prompt"))
        elif messages := request.get("messages"):
            prompt_tokens = 0
            for m in messages:
                content = m.get("content")
                if isinstance(content, str):
                    prompt_tokens += anthropic.count_tokens(content)
                elif isinstance(content, list):
                    for item in content:
                        # TODO: handle image and tool tokens
                        if isinstance(item, dict) and item.get("type") == "text":
                            prompt_tokens += anthropic.count_tokens(
                                item.get("text", "")
                            )
    return prompt_tokens


@dont_throw
async def acount_prompt_tokens_from_request(anthropic, request):
    prompt_tokens = 0
    if hasattr(anthropic, "count_tokens"):
        if request.get("prompt"):
            prompt_tokens = await anthropic.count_tokens(request.get("prompt"))
        elif messages := request.get("messages"):
            prompt_tokens = 0
            for m in messages:
                content = m.get("content")
                if isinstance(content, str):
                    prompt_tokens += await anthropic.count_tokens(content)
                elif isinstance(content, list):
                    for item in content:
                        # TODO: handle image and tool tokens
                        if isinstance(item, dict) and item.get("type") == "text":
                            prompt_tokens += await anthropic.count_tokens(
                                item.get("text", "")
                            )
    return prompt_tokens


def _create_metrics(meter: Meter):
    token_histogram = meter.create_histogram(
        name=Meters.LLM_TOKEN_USAGE,
        unit="token",
        description="Measures number of input and output tokens used",
    )

    choice_counter = meter.create_counter(
        name=Meters.LLM_GENERATION_CHOICES,
        unit="choice",
        description="Number of choices returned by chat completions call",
    )

    duration_histogram = meter.create_histogram(
        name=Meters.LLM_OPERATION_DURATION,
        unit="s",
        description="GenAI operation duration",
    )

    exception_counter = meter.create_counter(
        name=Meters.LLM_ANTHROPIC_COMPLETION_EXCEPTIONS,
        unit="time",
        description="Number of exceptions occurred during chat completions",
    )

    return token_histogram, choice_counter, duration_histogram, exception_counter


def is_streaming_response(response):
    return isinstance(response, Stream | AsyncStream)


async def _dump_content(message_index, content, span):
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # If the content is a list of text blocks, concatenate them.
        # This is more commonly used in prompt caching.
        if all(item.get("type") == "text" for item in content):
            return "".join([item.get("text") for item in content])

        return json.dumps(content)


@dont_throw
async def _aset_input_attributes(span, kwargs):
    _set_span_attribute(span, SpanAttributes.LLM_REQUEST_MODEL, kwargs.get("model"))
    _set_span_attribute(
        span, SpanAttributes.LLM_REQUEST_MAX_TOKENS, kwargs.get("max_tokens_to_sample")
    )
    _set_span_attribute(
        span, SpanAttributes.LLM_REQUEST_TEMPERATURE, kwargs.get("temperature")
    )
    _set_span_attribute(span, SpanAttributes.LLM_REQUEST_TOP_P, kwargs.get("top_p"))
    _set_span_attribute(
        span, SpanAttributes.LLM_FREQUENCY_PENALTY, kwargs.get("frequency_penalty")
    )
    _set_span_attribute(
        span, SpanAttributes.LLM_PRESENCE_PENALTY, kwargs.get("presence_penalty")
    )
    _set_span_attribute(span, SpanAttributes.LLM_IS_STREAMING, kwargs.get("stream"))

    if kwargs.get("prompt") is not None:
        _set_span_attribute(
            span, f"{SpanAttributes.LLM_PROMPTS}.0.user", kwargs.get("prompt")
        )

    elif kwargs.get("messages") is not None:
        for i, message in enumerate(kwargs.get("messages")):
            content = await _dump_content(
                message_index=i, span=span, content=message.get("content")
            )
            _set_span_attribute(
                span, f"{SpanAttributes.LLM_PROMPTS}.{i}.content", content
            )
            _set_span_attribute(
                span, f"{SpanAttributes.LLM_PROMPTS}.{i}.role", message.get("role")
            )

    if kwargs.get("tools") is not None:
        for i, tool in enumerate(kwargs.get("tools")):
            prefix = f"{SpanAttributes.LLM_REQUEST_FUNCTIONS}.{i}"
            _set_span_attribute(span, f"{prefix}.name", tool.get("name"))
            _set_span_attribute(span, f"{prefix}.description", tool.get("description"))
            input_schema = tool.get("input_schema")
            if input_schema is not None:
                _set_span_attribute(
                    span, f"{prefix}.input_schema", json.dumps(input_schema)
                )


def _set_span_completions(span, response):
    index = 0
    prefix = f"{SpanAttributes.LLM_COMPLETIONS}.{index}"
    _set_span_attribute(span, f"{prefix}.finish_reason", response.get("stop_reason"))
    if response.get("role"):
        _set_span_attribute(span, f"{prefix}.role", response.get("role"))
    if response.get("completion"):
        _set_span_attribute(span, f"{prefix}.content", response.get("completion"))
    elif response.get("content"):
        tool_call_index = 0
        text = ""
        for content in response.get("content"):
            content_block_type = content.type
            # usually, Antrhopic responds with just one text block,
            # but the API allows for multiple text blocks, so concatenate them
            if content_block_type == "text":
                text += content.text
            elif content_block_type == "tool_use":
                content = dict(content)
                _set_span_attribute(
                    span,
                    f"{prefix}.tool_calls.{tool_call_index}.id",
                    content.get("id"),
                )
                _set_span_attribute(
                    span,
                    f"{prefix}.tool_calls.{tool_call_index}.name",
                    content.get("name"),
                )
                tool_arguments = content.get("input")
                if tool_arguments is not None:
                    _set_span_attribute(
                        span,
                        f"{prefix}.tool_calls.{tool_call_index}.arguments",
                        json.dumps(tool_arguments),
                    )
                tool_call_index += 1
        _set_span_attribute(span, f"{prefix}.content", text)


@dont_throw
async def _aset_token_usage(
    span,
    anthropic,
    request,
    response,
    metric_attributes: dict | None,
    token_histogram: Histogram | None = None,
    choice_counter: Counter | None = None,
):
    if not metric_attributes:
        metric_attributes = {}
    if not isinstance(response, dict):
        response = response.__dict__

    if usage := response.get("usage"):
        prompt_tokens = usage.input_tokens
    else:
        prompt_tokens = await acount_prompt_tokens_from_request(anthropic, request)

    if usage := response.get("usage"):
        cache_read_tokens = dict(usage).get("cache_read_input_tokens", 0)
    else:
        cache_read_tokens = 0

    if usage := response.get("usage"):
        cache_creation_tokens = dict(usage).get("cache_creation_input_tokens", 0)
    else:
        cache_creation_tokens = 0

    input_tokens = prompt_tokens + cache_read_tokens + cache_creation_tokens

    if token_histogram and type(input_tokens) is int and input_tokens >= 0:
        token_histogram.record(
            input_tokens,
            attributes={
                **metric_attributes,
                SpanAttributes.LLM_TOKEN_TYPE: "input",
            },
        )

    if usage := response.get("usage"):
        completion_tokens = usage.output_tokens
    else:
        completion_tokens = 0
        if hasattr(anthropic, "count_tokens"):
            if response.get("completion"):
                completion_tokens = await anthropic.count_tokens(
                    response.get("completion")
                )
            elif response.get("content"):
                completion_tokens = await anthropic.count_tokens(
                    response.get("content")[0].text  # pyright: ignore
                )

    if token_histogram and type(completion_tokens) is int and completion_tokens >= 0:
        token_histogram.record(
            completion_tokens,
            attributes={
                **metric_attributes,
                SpanAttributes.LLM_TOKEN_TYPE: "output",
            },
        )

    total_tokens = input_tokens + completion_tokens

    choices = 0
    if type(response.get("content")) is list:
        choices = len(response.get("content"))  # pyright: ignore
    elif response.get("completion"):
        choices = 1

    if choices > 0 and choice_counter:
        choice_counter.add(
            choices,
            attributes={
                **metric_attributes,
                SpanAttributes.LLM_RESPONSE_STOP_REASON: response.get("stop_reason"),
            },  # pyright: ignore
        )

    _set_span_attribute(span, SpanAttributes.LLM_USAGE_PROMPT_TOKENS, input_tokens)
    _set_span_attribute(
        span, SpanAttributes.LLM_USAGE_COMPLETION_TOKENS, completion_tokens
    )
    _set_span_attribute(span, SpanAttributes.LLM_USAGE_TOTAL_TOKENS, total_tokens)

    _set_span_attribute(
        span,
        SpanAttributes.LLM_USAGE_CACHE_READ_INPUT_TOKENS,  # pyright: ignore
        cache_read_tokens,
    )
    _set_span_attribute(
        span,
        SpanAttributes.LLM_USAGE_CACHE_CREATION_INPUT_TOKENS,  # pyright: ignore
        cache_creation_tokens,
    )


@dont_throw
def _set_token_usage(
    span,
    anthropic,
    request,
    response,
    metric_attributes: dict | None = None,
    token_histogram: Histogram | None = None,
    choice_counter: Counter | None = None,
):
    if not metric_attributes:
        metric_attributes = {}

    if not isinstance(response, dict):
        response = response.__dict__

    if usage := response.get("usage"):
        prompt_tokens = usage.input_tokens
    else:
        prompt_tokens = count_prompt_tokens_from_request(anthropic, request)

    if usage := response.get("usage"):
        cache_read_tokens = dict(usage).get("cache_read_input_tokens", 0)
    else:
        cache_read_tokens = 0

    if usage := response.get("usage"):
        cache_creation_tokens = dict(usage).get("cache_creation_input_tokens", 0)
    else:
        cache_creation_tokens = 0

    input_tokens = prompt_tokens + cache_read_tokens + cache_creation_tokens

    if token_histogram and type(input_tokens) is int and input_tokens >= 0:
        token_histogram.record(
            input_tokens,
            attributes={
                **metric_attributes,
                SpanAttributes.LLM_TOKEN_TYPE: "input",
            },
        )

    if usage := response.get("usage"):
        completion_tokens = usage.output_tokens
    else:
        completion_tokens = 0
        if hasattr(anthropic, "count_tokens"):
            if response.get("completion"):
                completion_tokens = anthropic.count_tokens(response.get("completion"))
            elif response.get("content"):
                completion_tokens = anthropic.count_tokens(
                    response.get("content")[0].text  # pyright: ignore
                )

    if token_histogram and type(completion_tokens) is int and completion_tokens >= 0:
        token_histogram.record(
            completion_tokens,
            attributes={
                **metric_attributes,
                SpanAttributes.LLM_TOKEN_TYPE: "output",
            },
        )

    total_tokens = input_tokens + completion_tokens

    choices = 0
    if type(response.get("content")) is list:
        choices = len(response.get("content"))  # pyright: ignore
    elif response.get("completion"):
        choices = 1

    if choices > 0 and choice_counter:
        choice_counter.add(
            choices,
            attributes={
                **metric_attributes,
                SpanAttributes.LLM_RESPONSE_STOP_REASON: response.get("stop_reason"),
            },  # pyright: ignore
        )

    _set_span_attribute(span, SpanAttributes.LLM_USAGE_PROMPT_TOKENS, input_tokens)
    _set_span_attribute(
        span, SpanAttributes.LLM_USAGE_COMPLETION_TOKENS, completion_tokens
    )
    _set_span_attribute(span, SpanAttributes.LLM_USAGE_TOTAL_TOKENS, total_tokens)

    _set_span_attribute(
        span,
        SpanAttributes.LLM_USAGE_CACHE_READ_INPUT_TOKENS,  # pyright: ignore
        cache_read_tokens,
    )
    _set_span_attribute(
        span,
        SpanAttributes.LLM_USAGE_CACHE_CREATION_INPUT_TOKENS,  # pyright: ignore
        cache_creation_tokens,
    )


@dont_throw
def _set_response_attributes(span, response):
    if not isinstance(response, dict):
        response = response.__dict__
    _set_span_attribute(span, SpanAttributes.LLM_RESPONSE_MODEL, response.get("model"))

    if response.get("usage"):
        prompt_tokens = response.get("usage").input_tokens  # pyright: ignore
        completion_tokens = response.get("usage").output_tokens  # pyright: ignore
        _set_span_attribute(span, SpanAttributes.LLM_USAGE_PROMPT_TOKENS, prompt_tokens)
        _set_span_attribute(
            span, SpanAttributes.LLM_USAGE_COMPLETION_TOKENS, completion_tokens
        )
        _set_span_attribute(
            span,
            SpanAttributes.LLM_USAGE_TOTAL_TOKENS,
            prompt_tokens + completion_tokens,
        )

    _set_span_completions(span, response)


def _with_chat_telemetry_wrapper(func):
    """Helper for providing tracer for wrapper functions. Includes metric collectors."""

    def _with_chat_telemetry(
        tracer,
        token_histogram,
        choice_counter,
        duration_histogram,
        exception_counter,
        to_wrap,
    ):
        def wrapper(wrapped, instance, args, kwargs):
            return func(
                tracer,
                token_histogram,
                choice_counter,
                duration_histogram,
                exception_counter,
                to_wrap,
                wrapped,
                instance,
                args,
                kwargs,
            )

        return wrapper

    return _with_chat_telemetry


def _is_base64_image(item: dict[str, Any]) -> bool:
    if not isinstance(item, dict):
        return False

    if not isinstance(item.get("source"), dict):
        return False

    return not (item.get("type") != "image" or item["source"].get("type") != "base64")


@_with_chat_telemetry_wrapper
def _wrap(
    tracer: Tracer,
    token_histogram: Histogram,
    choice_counter: Counter,
    duration_histogram: Histogram,
    exception_counter: Counter,
    to_wrap,
    wrapped,
    instance,
    args,
    kwargs,
):
    """Instruments and calls every function defined in TO_WRAP."""
    if context_api.get_value(_SUPPRESS_INSTRUMENTATION_KEY) or context_api.get_value(
        SUPPRESS_LANGUAGE_MODEL_INSTRUMENTATION_KEY
    ):
        return wrapped(*args, **kwargs)

    name = to_wrap.get("span_name")
    span = tracer.start_span(
        name,
        kind=SpanKind.CLIENT,
        attributes={
            SpanAttributes.LLM_SYSTEM: "Anthropic",
            SpanAttributes.LLM_REQUEST_TYPE: LLMRequestTypeValues.COMPLETION.value,
        },
    )

    if span.is_recording():
        run_async(_aset_input_attributes(span, kwargs))

    start_time = time.time()
    try:
        response = wrapped(*args, **kwargs)
    except Exception as e:  # pylint: disable=broad-except
        end_time = time.time()
        attributes = error_metrics_attributes(e)

        if duration_histogram:
            duration = end_time - start_time
            duration_histogram.record(duration, attributes=attributes)

        if exception_counter:
            exception_counter.add(1, attributes=attributes)

        raise e

    end_time = time.time()

    if is_streaming_response(response):
        return build_from_streaming_response(
            span,
            response,
            instance._client,
            start_time,
            token_histogram,
            choice_counter,
            duration_histogram,
            exception_counter,
            kwargs,
        )
    elif response:
        try:
            metric_attributes = shared_metrics_attributes(response)

            if duration_histogram:
                duration = time.time() - start_time
                duration_histogram.record(
                    duration,
                    attributes=metric_attributes,
                )

            if span.is_recording():
                _set_response_attributes(span, response)
                _set_token_usage(
                    span,
                    instance._client,
                    kwargs,
                    response,
                    metric_attributes,
                    token_histogram,
                    choice_counter,
                )

        except Exception as ex:  # pylint: disable=broad-except
            logger.warning(
                "Failed to set response attributes for anthropic span, error: %s",
                str(ex),
            )
        if span.is_recording():
            span.set_status(Status(StatusCode.OK))
    span.end()
    return response


@_with_chat_telemetry_wrapper
async def _awrap(
    tracer,
    token_histogram: Histogram,
    choice_counter: Counter,
    duration_histogram: Histogram,
    exception_counter: Counter,
    to_wrap,
    wrapped,
    instance,
    args,
    kwargs,
):
    """Instruments and calls every function defined in TO_WRAP."""
    if context_api.get_value(_SUPPRESS_INSTRUMENTATION_KEY) or context_api.get_value(
        SUPPRESS_LANGUAGE_MODEL_INSTRUMENTATION_KEY
    ):
        return await wrapped(*args, **kwargs)

    name = to_wrap.get("span_name")
    span = tracer.start_span(
        name,
        kind=SpanKind.CLIENT,
        attributes={
            SpanAttributes.LLM_SYSTEM: "Anthropic",
            SpanAttributes.LLM_REQUEST_TYPE: LLMRequestTypeValues.COMPLETION.value,
        },
    )
    try:
        if span.is_recording():
            await _aset_input_attributes(span, kwargs)

    except Exception as ex:  # pylint: disable=broad-except
        logger.warning(
            "Failed to set input attributes for anthropic span, error: %s", str(ex)
        )

    start_time = time.time()
    try:
        response = await wrapped(*args, **kwargs)
    except Exception as e:  # pylint: disable=broad-except
        end_time = time.time()
        attributes = error_metrics_attributes(e)

        if duration_histogram:
            duration = end_time - start_time
            duration_histogram.record(duration, attributes=attributes)

        if exception_counter:
            exception_counter.add(1, attributes=attributes)

        raise e

    if is_streaming_response(response):
        return abuild_from_streaming_response(
            span,
            response,
            instance._client,
            start_time,
            token_histogram,
            choice_counter,
            duration_histogram,
            exception_counter,
            kwargs,
        )
    elif response:
        metric_attributes = shared_metrics_attributes(response)

        if duration_histogram:
            duration = time.time() - start_time
            duration_histogram.record(
                duration,
                attributes=metric_attributes,
            )

        if span.is_recording():
            _set_response_attributes(span, response)
            await _aset_token_usage(
                span,
                instance._client,
                kwargs,
                response,
                metric_attributes,
                token_histogram,
                choice_counter,
            )

        if span.is_recording():
            span.set_status(Status(StatusCode.OK))
    span.end()
    return response


def is_metrics_enabled() -> bool:
    return (os.getenv("TRACELOOP_METRICS_ENABLED") or "true").lower() == "true"


class AnthropicInstrumentor(BaseInstrumentor):
    """An instrumentor for Anthropic's client library."""

    def __init__(
        self,
        enrich_token_usage: bool = False,
        exception_logger=None,
        get_common_metrics_attributes: Callable[[], dict] = lambda: {},
        upload_base64_image: Callable[[str, str, str, str], Coroutine[None, None, str]]
        | None = None,
    ):
        super().__init__()

    def instrumentation_dependencies(self) -> Collection[str]:
        return _instruments

    def _instrument(self, **kwargs):
        tracer_provider = kwargs.get("tracer_provider")
        tracer = get_tracer(__name__, "0.0.1", tracer_provider)

        meter_provider = kwargs.get("meter_provider")
        meter = get_meter(__name__, "0.0.1", meter_provider)
        if is_metrics_enabled():
            (
                token_histogram,
                choice_counter,
                duration_histogram,
                exception_counter,
            ) = _create_metrics(meter)
        else:
            (
                token_histogram,
                choice_counter,
                duration_histogram,
                exception_counter,
            ) = (None, None, None, None)

        for wrapped_method in WRAPPED_METHODS:
            wrap_package = wrapped_method.get("package")
            wrap_object = wrapped_method.get("object")
            wrap_method = wrapped_method.get("method")

            with contextlib.suppress(
                ModuleNotFoundError
            ):  # that's ok, we don't want to fail if some methods do not exist
                wrap_function_wrapper(
                    wrap_package,
                    f"{wrap_object}.{wrap_method}",
                    _wrap(
                        tracer,
                        token_histogram,
                        choice_counter,
                        duration_histogram,
                        exception_counter,
                        wrapped_method,
                    ),  # pyright: ignore
                )

        for wrapped_method in WRAPPED_AMETHODS:
            wrap_package = wrapped_method.get("package")
            wrap_object = wrapped_method.get("object")
            wrap_method = wrapped_method.get("method")
            with contextlib.suppress(
                ModuleNotFoundError
            ):  # that's ok, we don't want to fail if some methods do not exist
                wrap_function_wrapper(
                    wrap_package,
                    f"{wrap_object}.{wrap_method}",
                    _awrap(
                        tracer,
                        token_histogram,
                        choice_counter,
                        duration_histogram,
                        exception_counter,
                        wrapped_method,
                    ),  # pyright: ignore
                )

    def _uninstrument(self, **kwargs):
        for wrapped_method in WRAPPED_METHODS:
            wrap_package = wrapped_method.get("package")
            wrap_object = wrapped_method.get("object")
            unwrap(
                f"{wrap_package}.{wrap_object}",
                wrapped_method.get("method"),
            )
        for wrapped_method in WRAPPED_AMETHODS:
            wrap_package = wrapped_method.get("package")
            wrap_object = wrapped_method.get("object")
            unwrap(
                f"{wrap_package}.{wrap_object}",
                wrapped_method.get("method"),
            )
