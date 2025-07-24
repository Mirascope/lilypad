"""Utilities for middleware for Lilypad prompts and Mirascope calls."""

from __future__ import annotations

import base64
import logging
from io import BytesIO
from uuid import UUID
from typing import TYPE_CHECKING, Any, TypeVar, NoReturn, ParamSpec, cast
from contextlib import contextmanager, _GeneratorContextManager
from collections.abc import Callable, Generator

import orjson
from pydantic import BaseModel
from mirascope.core import base as mb
from opentelemetry.trace import Span, Status, StatusCode, SpanContext, get_tracer
from .mirascope_middleware_factory import middleware_factory
from opentelemetry.util.types import AttributeValue
from mirascope.integrations._middleware_factory import SyncFunc, AsyncFunc

from .json import json_dumps, fast_jsonable
from .settings import get_settings
from .functions import ArgTypes, ArgValues

if TYPE_CHECKING:
    from ..generated.types.function_public import FunctionPublic


_P = ParamSpec("_P")
_R = TypeVar("_R")


try:
    import PIL
    import PIL.WebPImagePlugin
except ImportError:

    class PIL:
        class WebPImagePlugin:
            class WebPImageFile:
                def save(self, *args: Any, **kwargs: Any) -> NoReturn:
                    raise NotImplementedError("Pillow is not installed. Please install Pillow to use this feature.")


logger = logging.getLogger(__name__)


class AsyncCompatibleSpanWrapper:
    """Wrapper for NonRecordingSpan to make it async-compatible."""

    def __init__(self, span: Span):
        self._span = span

    def __getattr__(self, name: str) -> Any:
        """Delegate all other attributes to the wrapped span."""
        return getattr(self._span, name)

    async def __aenter__(self) -> "AsyncCompatibleSpanWrapper":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if hasattr(self._span, "__exit__"):
            self._span.__exit__(exc_type, exc_val, exc_tb)


class SpanContextHolder:
    """Holds the OpenTelemetry SpanContext."""

    def __init__(self) -> None:
        self._span_context: SpanContext | None = None

    def set_span_context(self, span: Span) -> None:
        self._span_context = span.get_span_context()

    @property
    def span_context(self) -> SpanContext | None:
        return self._span_context


def _get_custom_context_manager(
    function: FunctionPublic | None,
    arg_types: ArgTypes,
    arg_values: ArgValues,
    is_async: bool,
    prompt_template: str | None = None,
    project_uuid: UUID | None = None,
    span_context_holder: SpanContextHolder | None = None,
    current_span: Span | None = None,
    decorator_tags: list[str] | None = None,
) -> Callable[..., _GeneratorContextManager[Span]]:
    @contextmanager
    def custom_context_manager(
        fn: SyncFunc | AsyncFunc,
    ) -> Generator[Span, Any, None]:
        new_project_uuid = project_uuid or get_settings().project_id
        jsonable_arg_values = {}
        for arg_name, arg_value in arg_values.items():
            try:
                serialized_arg_value = fast_jsonable(arg_value)
            except (TypeError, ValueError, orjson.JSONEncodeError):
                serialized_arg_value = "could not serialize"
            jsonable_arg_values[arg_name] = serialized_arg_value
        if current_span:
            _current_span = current_span
            create_span = False
        else:
            tracer = get_tracer("lilypad")
            span_cm = tracer.start_as_current_span(f"{fn.__name__}")
            _current_span = span_cm.__enter__()
            # Check if we got a NonRecordingSpan (happens when tracing is not configured)
            if hasattr(_current_span, "__class__") and _current_span.__class__.__name__ == "NonRecordingSpan":
                # NonRecordingSpan doesn't support async context manager protocol
                # Wrap it to make it async-compatible
                _current_span = AsyncCompatibleSpanWrapper(_current_span)
            create_span = True

        try:
            attributes: dict[str, AttributeValue] = {
                "lilypad.project_uuid": str(new_project_uuid) if new_project_uuid else "",
                "lilypad.is_async": is_async,
            }
            if decorator_tags is not None:
                attributes["lilypad.trace.tags"] = decorator_tags
            attribute_type = "mirascope.v1" if function else "trace"
            if function:
                attributes["lilypad.function.uuid"] = str(function.uuid_)
                attributes["lilypad.function.name"] = fn.__name__
                attributes["lilypad.function.signature"] = function.signature
                attributes["lilypad.function.code"] = function.code
                attributes["lilypad.function.arg_types"] = json_dumps(arg_types)
                attributes["lilypad.function.arg_values"] = json_dumps(jsonable_arg_values)
                attributes["lilypad.function.prompt_template"] = prompt_template or ""
                attributes["lilypad.function.version"] = function.version_num if function.version_num else -1
            attributes["lilypad.type"] = attribute_type
            attributes[f"lilypad.{attribute_type}.arg_types"] = json_dumps(arg_types)
            attributes[f"lilypad.{attribute_type}.arg_values"] = json_dumps(jsonable_arg_values)
            attributes[f"lilypad.{attribute_type}.prompt_template"] = prompt_template or ""
            filtered_attributes = {k: v for k, v in attributes.items() if v is not None}
            if _current_span:
                _current_span.set_attributes(filtered_attributes)
                if span_context_holder:
                    span_context_holder.set_span_context(_current_span)
            yield _current_span

            if create_span and _current_span:
                # For Span objects, use the appropriate exit method
                # For NonRecordingSpan, it only has __exit__ not __aexit__
                if hasattr(_current_span, "__exit__"):
                    _current_span.__exit__(None, None, None)
        except Exception as error:
            if create_span and _current_span:
                if hasattr(_current_span, "__exit__"):
                    _current_span.__exit__(Exception, error, None)
            raise error

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


def safe_serialize(response_obj: Any) -> str:
    """
    Safely serialize a Pydantic object containing Protobuf fields without using model_dump
    """
    # Convert to JSON
    return json_dumps(recursive_process_value(response_obj))


def recursive_process_value(value: Any) -> dict | list | str | int | float | bool | None:
    """
    Recursively process any value to make it JSON serializable,
    with special handling for Protobuf objects
    """
    # Handle None
    if value is None:
        return None

    # Handle Protobuf objects
    if hasattr(value, "SerializeToString") and callable(value.SerializeToString):
        # Check if it's a properly structured Protobuf message
        if hasattr(value, "DESCRIPTOR") and hasattr(value, "ListFields"):
            # Proper Protobuf message with accessible fields
            proto_dict = {}
            for descriptor, field_value in value.ListFields():
                field_name = descriptor.name
                proto_dict[field_name] = recursive_process_value(field_value)
            return proto_dict
        else:
            return str(value)

    # Handle Pydantic models by accessing their __dict__
    if hasattr(value, "__dict__") and not isinstance(value, type):
        result = {}
        for field_name, field_value in value.__dict__.items():
            # Skip private fields and tool_types
            if field_name.startswith("_") or field_name == "tool_types":
                continue
            result[field_name] = recursive_process_value(field_value)
        return result

    # Handle basic types directly
    if isinstance(value, (str, int, float, bool)):
        return value

    # Handle lists
    if isinstance(value, list):
        return [recursive_process_value(item) for item in value]

    # Handle dictionaries
    if isinstance(value, dict):
        return {k: recursive_process_value(v) for k, v in value.items()}

    # Handle sets by converting to list
    if isinstance(value, set):
        return [recursive_process_value(item) for item in value]

    # Handle tuples by converting to list
    if isinstance(value, tuple):
        return [recursive_process_value(item) for item in value]

    # For any other type, convert to string
    return str(value)


def bytes_serializer(obj: bytes) -> str:
    """Serialize bytes to a base64 encoded string."""
    return base64.b64encode(obj).decode("utf-8")


def _set_call_response_attributes(response: mb.BaseCallResponse, span: Span | None, trace_type: str) -> None:
    if span is None:
        return
    try:
        output = safe_serialize(response)
    except TypeError:
        output = str(response)
    try:
        messages = fast_jsonable(
            response.common_messages + [response.common_message_param], custom_serializers={bytes: bytes_serializer}
        )
    except TypeError:
        messages = str(response.common_messages) + str(response.common_message_param)
    attributes: dict[str, AttributeValue] = {
        f"lilypad.{trace_type}.response": output,
        f"lilypad.{trace_type}.messages": messages,
    }
    span.set_attributes(attributes)


def _set_response_model_attributes(  # noqa: D401
    result: BaseModel | mb.BaseType,
    span: Span | None,
    trace_type: str,
) -> None:
    if span is None:
        return
    if isinstance(result, BaseModel):
        completion: str | int | float | bool | None = fast_jsonable(result)
        response_obj: mb.BaseCallResponse | None = getattr(result, "_response", None)
        _set_call_response_attributes(response_obj, span, trace_type)
    else:
        completion = result if isinstance(result, str | int | float | bool) else str(result)

    attr_key = f"lilypad.{trace_type}."
    attributes = {f"{attr_key}response_model": completion}

    span.set_attributes(attributes)


class _Handlers:
    def __init__(self, trace_type: str) -> None:
        self.trace_type = trace_type

    def handle_call_response(self, result: mb.BaseCallResponse, fn: Callable, span: Span | None) -> None:
        if span is None:
            return
        _set_call_response_attributes(result, span, self.trace_type)

    def handle_stream(self, stream: mb.BaseStream, fn: Callable, span: Span | None) -> None:
        if span is None:
            return
        call_response = cast(mb.BaseCallResponse, stream.construct_call_response())
        _set_call_response_attributes(call_response, span, self.trace_type)

    def handle_response_model(self, result: BaseModel | mb.BaseType, fn: Callable, span: Span | None) -> None:
        if span is None:
            return

        _set_response_model_attributes(result, span, self.trace_type)

    def handle_structured_stream(self, result: mb.BaseStructuredStream, fn: Callable, span: Span | None) -> None:
        if span is None:
            return

        _set_response_model_attributes(result.constructed_response_model, span, self.trace_type)

    async def handle_call_response_async(self, result: mb.BaseCallResponse, fn: Callable, span: Span | None) -> None:
        if span is None:
            return

        _set_call_response_attributes(result, span, self.trace_type)

    async def handle_stream_async(self, stream: mb.BaseStream, fn: Callable, span: Span | None) -> None:
        if span is None:
            return
        call_response = cast(mb.BaseCallResponse, stream.construct_call_response())
        _set_call_response_attributes(call_response, span, self.trace_type)

    async def handle_response_model_async(
        self, result: BaseModel | mb.BaseType, fn: Callable, span: Span | None
    ) -> None:
        if span is None:
            return
        _set_response_model_attributes(result, span, self.trace_type)

    async def handle_structured_stream_async(
        self, result: mb.BaseStructuredStream, fn: Callable, span: Span | None
    ) -> None:
        if span is None:
            return
        _set_response_model_attributes(result.constructed_response_model, span, self.trace_type)


def _handle_error(error: Exception, fn: SyncFunc | AsyncFunc, span: Span | None) -> None:
    """Records the exception on the span. Does not suppress the error."""
    if span and span.is_recording():
        span.record_exception(error)
        span.set_status(Status(StatusCode.ERROR, f"{type(error).__name__}: {error}"))
    elif span is None:
        fn_name = getattr(fn, "__name__", "unknown_function")
        logger.error(f"Error during sync execution of {fn_name} (span not available): {error}")


async def _handle_error_async(error: Exception, fn: SyncFunc | AsyncFunc, span: Span | None) -> None:
    """Records the exception on the span. Does not suppress the error."""
    _handle_error(error, fn, span)


def create_mirascope_middleware(
    function: FunctionPublic | None,
    arg_types: ArgTypes,
    arg_values: ArgValues,
    is_async: bool,
    prompt_template: str | None = None,
    project_uuid: UUID | None = None,
    span_context_holder: SpanContextHolder | None = None,
    current_span: Span | None = None,
    decorator_tags: list[str] | None = None,
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    """Creates the middleware decorator for a Lilypad/Mirascope function."""
    cm_callable: Callable[[SyncFunc | AsyncFunc], _GeneratorContextManager[Span]] = _get_custom_context_manager(
        function,
        arg_types,
        arg_values,
        is_async,
        prompt_template,
        project_uuid,
        span_context_holder,
        current_span,
        decorator_tags,
    )
    _handlers = _Handlers("mirascope.v1" if function else "trace")
    return middleware_factory(
        custom_context_manager=cm_callable,
        handle_call_response=_handlers.handle_call_response,
        handle_call_response_async=_handlers.handle_call_response_async,
        handle_stream=_handlers.handle_stream,
        handle_stream_async=_handlers.handle_stream_async,
        handle_response_model=_handlers.handle_response_model,
        handle_response_model_async=_handlers.handle_response_model_async,
        handle_structured_stream=_handlers.handle_structured_stream,
        handle_structured_stream_async=_handlers.handle_structured_stream_async,
        handle_error=_handle_error,
        handle_error_async=_handle_error_async,
    )


__all__ = ["SpanContextHolder", "create_mirascope_middleware"]
