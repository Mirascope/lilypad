import json
from collections.abc import Collection
from types import AsyncGeneratorType, GeneratorType
from typing import Any

from opentelemetry import context
from opentelemetry.context import _SUPPRESS_INSTRUMENTATION_KEY
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.utils import unwrap
from opentelemetry.trace import SpanKind, Tracer, get_tracer
from opentelemetry.trace.status import Status, StatusCode
from wrapt import wrap_function_wrapper

from lilypad._utils import encode_gemini_part

from ._utils import (
    SUPPRESS_LANGUAGE_MODEL_INSTRUMENTATION_KEY,
    LLMRequestTypeValues,
    Method,
    SpanAttributes,
    _set_span_attribute,
    _with_tracer_wrapper,
    dont_throw,
)

WRAPPED_METHODS: list[Method] = [
    Method(
        package="google.generativeai.generative_models",
        object="GenerativeModel",
        method="generate_content",
        span_name="gemini.generate_content",
    ),
    Method(
        package="google.generativeai.generative_models",
        object="GenerativeModel",
        method="generate_content_async",
        span_name="gemini.generate_content_async",
    ),
]


def _set_input_attributes(span, args, kwargs, llm_model):
    # TODO: Add support for multiple prompts
    if args is not None and len(args) > 0:
        prompt = ""
        for arg in args:
            if isinstance(arg, str):
                prompt = f"{prompt}{arg}\n"
            elif isinstance(arg, list):
                for subarg in arg:
                    prompt = f"{prompt}{subarg}\n"

        _set_span_attribute(
            span,
            f"{SpanAttributes.LLM_PROMPTS}.0.user",
            prompt,
        )
    elif kwargs is not None and "contents" in kwargs:
        for i, content in enumerate(kwargs["contents"]):
            json_part = [encode_gemini_part(part) for part in content.get("parts", [])]
            _set_span_attribute(
                span,
                f"{SpanAttributes.LLM_PROMPTS}.{i}.{content.get('role')}",
                json.dumps(json_part),
            )

    _set_span_attribute(span, SpanAttributes.LLM_REQUEST_MODEL, llm_model)
    _set_span_attribute(
        span, f"{SpanAttributes.LLM_PROMPTS}.0.user", kwargs.get("prompt")
    )
    _set_span_attribute(
        span, SpanAttributes.LLM_REQUEST_TEMPERATURE, kwargs.get("temperature")
    )
    _set_span_attribute(
        span, SpanAttributes.LLM_REQUEST_MAX_TOKENS, kwargs.get("max_output_tokens")
    )
    _set_span_attribute(span, SpanAttributes.LLM_REQUEST_TOP_P, kwargs.get("top_p"))
    _set_span_attribute(span, SpanAttributes.LLM_TOP_K, kwargs.get("top_k"))
    _set_span_attribute(
        span, SpanAttributes.LLM_PRESENCE_PENALTY, kwargs.get("presence_penalty")
    )
    _set_span_attribute(
        span, SpanAttributes.LLM_FREQUENCY_PENALTY, kwargs.get("frequency_penalty")
    )

    return


@dont_throw
def _set_response_attributes(span, response, llm_model):
    _set_span_attribute(span, SpanAttributes.LLM_RESPONSE_MODEL, llm_model)

    if hasattr(response, "usage_metadata"):
        _set_span_attribute(
            span,
            SpanAttributes.LLM_USAGE_TOTAL_TOKENS,
            response.usage_metadata.total_token_count,
        )
        _set_span_attribute(
            span,
            SpanAttributes.LLM_USAGE_COMPLETION_TOKENS,
            response.usage_metadata.candidates_token_count,
        )
        _set_span_attribute(
            span,
            SpanAttributes.LLM_USAGE_PROMPT_TOKENS,
            response.usage_metadata.prompt_token_count,
        )

        if isinstance(response.text, list):
            for index, item in enumerate(response):
                prefix = f"{SpanAttributes.LLM_COMPLETIONS}.{index}"
                _set_span_attribute(span, f"{prefix}.content", item.text)
        elif isinstance(response.text, str):
            _set_span_attribute(
                span, f"{SpanAttributes.LLM_COMPLETIONS}.0.content", response.text
            )
    else:
        if isinstance(response, list):
            for index, item in enumerate(response):
                prefix = f"{SpanAttributes.LLM_COMPLETIONS}.{index}"
                _set_span_attribute(span, f"{prefix}.content", item)
        elif isinstance(response, str):
            _set_span_attribute(
                span, f"{SpanAttributes.LLM_COMPLETIONS}.0.content", response
            )

    return


@dont_throw
def _handle_request(span, args, kwargs, llm_model):
    if span.is_recording():
        _set_input_attributes(span, args, kwargs, llm_model)


@dont_throw
def _handle_response(span, response, llm_model):
    if span.is_recording():
        _set_response_attributes(span, response, llm_model)

        span.set_status(Status(StatusCode.OK))


def is_streaming_response(response):
    return isinstance(response, GeneratorType)


def is_async_streaming_response(response):
    return isinstance(response, AsyncGeneratorType)


def _build_from_streaming_response(span, response, llm_model):
    complete_response = ""
    for item in response:
        item_to_yield = item
        complete_response += str(item.text)

        yield item_to_yield

    _set_response_attributes(span, complete_response, llm_model)

    span.set_status(Status(StatusCode.OK))
    span.end()


async def _abuild_from_streaming_response(span, response, llm_model):
    complete_response = ""
    async for item in response:
        item_to_yield = item
        complete_response += str(item.text)

        yield item_to_yield

    _set_response_attributes(span, complete_response, llm_model)

    span.set_status(Status(StatusCode.OK))
    span.end()


@_with_tracer_wrapper
def _wrap(
    tracer: Tracer,
    to_wrap: Method,
    wrapped,
    instance: Any | None,
    args,
    kwargs,
):
    """Instruments and calls every function defined in TO_WRAP."""
    if context.get_value(_SUPPRESS_INSTRUMENTATION_KEY) or context.get_value(
        SUPPRESS_LANGUAGE_MODEL_INSTRUMENTATION_KEY
    ):
        return wrapped(*args, **kwargs)

    llm_model = "unknown"
    if hasattr(instance, "_model_id"):
        llm_model = instance._model_id  # pyright: ignore
    if hasattr(instance, "_model_name"):
        llm_model = instance._model_name.replace("publishers/google/models/", "")  # pyright: ignore
    name = to_wrap["span_name"]
    span = tracer.start_span(
        name,
        kind=SpanKind.CLIENT,
        attributes={
            SpanAttributes.LLM_SYSTEM: "Gemini",
            SpanAttributes.LLM_REQUEST_TYPE: LLMRequestTypeValues.COMPLETION,
        },
    )

    _handle_request(span, args, kwargs, llm_model)
    response = wrapped(*args, **kwargs)

    if response:
        if is_streaming_response(response):
            return _build_from_streaming_response(span, response, llm_model)
        elif is_async_streaming_response(response):
            return _abuild_from_streaming_response(span, response, llm_model)
        else:
            _handle_response(span, response, llm_model)

    span.end()
    return response


@_with_tracer_wrapper
async def _awrap(
    tracer: Tracer,
    to_wrap: Method,
    wrapped,
    instance: Any | None,
    args,
    kwargs,
):
    """Instruments and calls every function defined in TO_WRAP."""
    if context.get_value(_SUPPRESS_INSTRUMENTATION_KEY) or context.get_value(
        SUPPRESS_LANGUAGE_MODEL_INSTRUMENTATION_KEY
    ):
        return await wrapped(*args, **kwargs)

    llm_model = "unknown"
    if hasattr(instance, "_model_id"):
        llm_model = instance._model_id  # pyright: ignore
    if hasattr(instance, "_model_name"):
        llm_model = instance._model_name.replace("publishers/google/models/", "")  # pyright: ignore

    name = to_wrap["span_name"]
    span = tracer.start_span(
        name,
        kind=SpanKind.CLIENT,
        attributes={
            SpanAttributes.LLM_SYSTEM: "Gemini",
            SpanAttributes.LLM_REQUEST_TYPE: LLMRequestTypeValues.COMPLETION,
        },
    )

    _handle_request(span, args, kwargs, llm_model)

    response = await wrapped(*args, **kwargs)

    if response:
        if is_streaming_response(response):
            return _build_from_streaming_response(span, response, llm_model)
        elif is_async_streaming_response(response):
            return _abuild_from_streaming_response(span, response, llm_model)
        else:
            _handle_response(span, response, llm_model)

    span.end()
    return response


class GoogleGenerativeAiInstrumentor(BaseInstrumentor):
    def instrumentation_dependencies(self) -> Collection[str]:
        return ["google-generativeai>=0.4.0"]

    def _instrument(self, **kwargs):
        tracer_provider = kwargs.get("tracer_provider")
        tracer = get_tracer(__name__, "0.0.1", tracer_provider)
        for wrapped_method in WRAPPED_METHODS:
            wrap_function_wrapper(
                wrapped_method["package"],
                f"{wrapped_method['object']}.{wrapped_method['method']}",
                (
                    _awrap(tracer, wrapped_method)  # pyright: ignore
                    if wrapped_method["method"] == "generate_content_async"
                    else _wrap(tracer, wrapped_method)  # pyright: ignore
                ),
            )

    def _uninstrument(self, **kwargs):
        for wrapped_method in WRAPPED_METHODS:
            wrap_package = wrapped_method["package"]
            wrap_object = wrapped_method["object"]
            unwrap(
                f"{wrap_package}.{wrap_object}",
                wrapped_method["method"],
            )
