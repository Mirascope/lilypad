"""Utilities for middleware for Lilypad prompts and Mirascope calls."""

import base64
import json
from collections.abc import Callable, Generator
from contextlib import _GeneratorContextManager, contextmanager
from io import BytesIO
from typing import Any, ParamSpec, TypeVar, cast
from uuid import UUID

import PIL
import PIL.WebPImagePlugin
from mirascope.core import base as mb
from mirascope.integrations import middleware_factory
from opentelemetry.trace import get_tracer
from opentelemetry.trace.span import Span
from opentelemetry.util.types import AttributeValue
from pydantic import BaseModel

from ..server.client import LilypadClient
from ..server.models import GenerationPublic

_P = ParamSpec("_P")
_R = TypeVar("_R")


def _get_custom_context_manager(
    generation: GenerationPublic,
    arg_types: dict[str, str],
    arg_values: dict[str, Any],
    is_async: bool,
    prompt_template: str | None = None,
    project_uuid: UUID | None = None,
) -> Callable[..., _GeneratorContextManager[Span]]:
    @contextmanager
    def custom_context_manager(
        fn: Callable,
    ) -> Generator[Span, Any, None]:
        tracer = get_tracer("lilypad")
        lilypad_client = LilypadClient(timeout=10)
        new_project_uuid = project_uuid or lilypad_client.project_uuid
        with tracer.start_as_current_span(f"{fn.__name__}") as span:
            attributes: dict[str, AttributeValue] = {
                "lilypad.project_uuid": str(new_project_uuid)
                if new_project_uuid
                else "",
                "lilypad.type": "generation",
                "lilypad.generation.uuid": str(generation.uuid),
                "lilypad.generation.name": fn.__name__,
                "lilypad.generation.signature": generation.signature,
                "lilypad.generation.code": generation.code,
                "lilypad.generation.arg_types": json.dumps(arg_types),
                "lilypad.generation.arg_values": json.dumps(arg_values),
                "lilypad.generation.prompt_template": prompt_template or "",
                "lilypad.is_async": is_async,
            }
            span.set_attributes(attributes)
            yield span

    return custom_context_manager


def encode_gemini_part(
    part: str | dict | PIL.WebPImagePlugin.WebPImageFile,
) -> str | dict:
    if isinstance(part, dict):
        if "mime_type" in part and "data" in part:
            # Handle binary data by base64 encoding it
            return {
                "mime_type": part["mime_type"],
                "data": base64.b64encode(part["data"]).decode("utf-8"),
            }
        return part
    elif isinstance(part, PIL.WebPImagePlugin.WebPImageFile):
        buffered = BytesIO()
        part.save(buffered, format="WEBP")  # Use "WEBP" to maintain the original format
        img_bytes = buffered.getvalue()
        return {
            "mime_type": "image/webp",
            "data": base64.b64encode(img_bytes).decode("utf-8"),
        }
    return part


def _default_serializer(obj: Any) -> Any:
    if hasattr(obj, "role") and hasattr(obj, "content"):
        return {
            "role": obj.role,
            "content": obj.content,
        }
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def _serialize_proto_data(data: list[dict]) -> str:
    serializable_data = []
    for item in data:
        if not isinstance(item, dict):
            item = _default_serializer(item)

        serialized_item = item.copy()
        if "parts" in item:
            serialized_item["parts"] = [
                encode_gemini_part(part) for part in item["parts"]
            ]
        serializable_data.append(serialized_item)

    return json.dumps(serializable_data, default=_default_serializer)


def _set_call_response_attributes(response: mb.BaseCallResponse, span: Span) -> None:
    try:
        output = json.dumps(response.message_param, default=_default_serializer)
    except TypeError:
        output = str(response.message_param)
    try:
        messages = json.dumps(response.messages, default=_default_serializer)
    except TypeError:
        converted_messages = []
        for m in response.messages:
            if isinstance(m, dict):
                converted_messages.append(m)
            else:
                converted_messages.append(_default_serializer(m))
        messages = _serialize_proto_data(converted_messages)

    attributes: dict[str, AttributeValue] = {
        "lilypad.generation.output": output,
        "lilypad.generation.messages": messages,
    }
    span.set_attributes(attributes)


def _set_response_model_attributes(result: BaseModel | mb.BaseType, span: Span) -> None:
    if isinstance(result, BaseModel):
        completion = result.model_dump_json()
        # Attempt to serialize messages if _response and _response.messages exist
        if (_response := getattr(result, "_response", None)) and (
            _response_messages := getattr(_response, "messages", None)
        ):
            try:
                messages = json.dumps(_response_messages, default=_default_serializer)
            except TypeError:
                # If serialization fails, try fallback
                if isinstance(_response_messages, list):
                    converted_msgs = []
                    for m in _response_messages:
                        if isinstance(m, dict):
                            converted_msgs.append(m)
                        else:
                            converted_msgs.append(_default_serializer(m))
                    messages = _serialize_proto_data(converted_msgs)
                else:
                    messages = str(_response_messages)
        else:
            messages = None
    else:
        if not isinstance(result, str | int | float | bool):
            result = str(result)
        completion = result
        messages = None

    attributes: dict[str, AttributeValue] = {
        "lilypad.generation.output": completion,
    }
    if messages:
        attributes["lilypad.generation.messages"] = messages
    span.set_attributes(attributes)


def _handle_call_response(
    result: mb.BaseCallResponse, fn: Callable, span: Span | None
) -> None:
    if span is None:
        return
    _set_call_response_attributes(result, span)


def _handle_stream(stream: mb.BaseStream, fn: Callable, span: Span | None) -> None:
    if span is None:
        return
    call_response = cast(mb.BaseCallResponse, stream.construct_call_response())
    _set_call_response_attributes(call_response, span)


def _handle_response_model(
    result: BaseModel | mb.BaseType, fn: Callable, span: Span | None
) -> None:
    if span is None:
        return

    _set_response_model_attributes(result, span)


def _handle_structured_stream(
    result: mb.BaseStructuredStream, fn: Callable, span: Span | None
) -> None:
    if span is None:
        return

    _set_response_model_attributes(result.constructed_response_model, span)


async def _handle_call_response_async(
    result: mb.BaseCallResponse, fn: Callable, span: Span | None
) -> None:
    if span is None:
        return

    _set_call_response_attributes(result, span)


async def _handle_stream_async(
    stream: mb.BaseStream, fn: Callable, span: Span | None
) -> None:
    if span is None:
        return
    call_response = cast(mb.BaseCallResponse, stream.construct_call_response())
    _set_call_response_attributes(call_response, span)


async def _handle_response_model_async(
    result: BaseModel | mb.BaseType, fn: Callable, span: Span | None
) -> None:
    if span is None:
        return
    _set_response_model_attributes(result, span)


async def _handle_structured_stream_async(
    result: mb.BaseStructuredStream, fn: Callable, span: Span | None
) -> None:
    if span is None:
        return
    _set_response_model_attributes(result.constructed_response_model, span)


def create_mirascope_middleware(
    generation: GenerationPublic,
    arg_types: dict[str, str],
    arg_values: dict[str, Any],
    is_async: bool,
    prompt_template: str | None = None,
    project_uuid: UUID | None = None,
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    """Creates the middleware decorator for a Lilypad/Mirascope function."""
    return middleware_factory(
        custom_context_manager=_get_custom_context_manager(
            generation, arg_types, arg_values, is_async, prompt_template, project_uuid
        ),
        handle_call_response=_handle_call_response,
        handle_call_response_async=_handle_call_response_async,
        handle_stream=_handle_stream,
        handle_stream_async=_handle_stream_async,
        handle_response_model=_handle_response_model,
        handle_response_model_async=_handle_response_model_async,
        handle_structured_stream=_handle_structured_stream,
        handle_structured_stream_async=_handle_structured_stream_async,
    )


__all__ = ["create_mirascope_middleware"]
