"""This module contains the `generation` decorator and related utilities for tracing."""

from __future__ import annotations

import os
import inspect
import logging
import threading
from types import MappingProxyType
from typing import (
    Any,
    Generic,
    Literal,
    TypeVar,
    Protocol,
    ParamSpec,
    TypeAlias,
    overload,
)
from functools import wraps
from contextlib import contextmanager
from contextvars import ContextVar
from collections.abc import Callable, Coroutine, Generator

import orjson
from pydantic import BaseModel
from opentelemetry.trace import format_span_id, get_tracer_provider, TracerProvider
from opentelemetry.util.types import AttributeValue

from .spans import Span
from ._utils import (
    Closure,
    call_safely,
    fn_is_async,
    inspect_arguments,
    get_qualified_name,
    create_mirascope_middleware,
)
from .sandbox import SandboxRunner, SubprocessSandboxRunner
import httpx
from .exceptions import RemoteFunctionError, LilypadException
from ._utils.json import to_text, json_dumps, fast_jsonable
from ._utils.client import get_sync_client, get_async_client
from ._utils.settings import get_settings
from ._utils.functions import get_signature
from .generated.client import Lilypad, AsyncLilypad
from ._utils.function_cache import (
    get_cached_closure,
    get_function_by_hash_sync,
    get_deployed_function_sync,
    get_function_by_hash_async,
    get_deployed_function_async,
    get_function_by_version_sync,
    get_function_by_version_async,
)
from .generated.types.label import Label
from ._utils.serializer_registry import SerializerMap
from .generated.types.evaluation_type import EvaluationType
from .generated.types.function_public import FunctionPublic
from .generated.errors.not_found_error import NotFoundError
from .generated.types.annotation_create import AnnotationCreate

_P = ParamSpec("_P")
_R = TypeVar("_R")
_R_CO = TypeVar("_R_CO", covariant=True)
_T = TypeVar("_T")


TRACE_MODULE_NAME = "lilypad.traces"
logger = logging.getLogger(__name__)

# Thread-safe warning flag
_trace_warning_lock = threading.Lock()
_trace_warning_shown = False


def _get_trace_type(function: FunctionPublic | None) -> Literal["trace", "function"]:
    if function:
        return "function"
    return "trace"


class Annotation(BaseModel):
    data: dict[str, Any] | None

    label: Label | None

    reasoning: str | None

    type: EvaluationType | None


class _TraceBase(Generic[_T]):
    """
    Base class for the Trace wrapper.
    """

    def __init__(self, response: _T, span_id: int, function_uuid: str) -> None:
        self.response: _T = response
        self.function_uuid: str = function_uuid
        self.formated_span_id: str = format_span_id(span_id)
        self._flush: bool = False

    def _force_flush(self) -> None:
        tracer = get_tracer_provider()
        if force_flush := getattr(tracer, "force_flush", None):
            force_flush(timeout_millis=5000)
            self._flush = True

    def _create_request(
        self, project_id: str, span_uuid: str, annotation: tuple[Annotation, ...]
    ) -> list[AnnotationCreate]:
        return [
            AnnotationCreate(
                data=annotation.data,
                function_uuid=self.function_uuid,
                span_uuid=span_uuid,
                label=annotation.label,
                reasoning=annotation.reasoning,
                type=annotation.type,
                project_uuid=project_id,
            )
            for annotation in annotation
        ]


class Trace(_TraceBase[_T]):
    """
    A simple trace wrapper that holds the original function's response and allows annotating the trace.
    """

    def _get_span_uuid(self, client: Lilypad) -> str | None:
        if not self._flush:
            self._force_flush()
        response = client.projects.functions.spans.list_paginated(
            project_uuid=get_settings().project_id, function_uuid=self.function_uuid
        )
        for span in response.items:
            if span.span_id == self.formated_span_id:
                return span.uuid_
        return None

    def annotate(self, *annotation: Annotation) -> None:
        """
        Annotate the trace with the given annotation.
        """
        if not annotation:
            raise ValueError("At least one annotation must be provided")

        settings = get_settings()
        lilypad_client = get_sync_client(api_key=settings.api_key)
        span_uuid = self._get_span_uuid(lilypad_client)

        if span_uuid is None:  # pragma: no cover
            from lilypad.exceptions import SpanNotFoundError

            raise SpanNotFoundError(f"Cannot annotate: span not found for function {self.function_uuid}")

        request = self._create_request(settings.project_id, span_uuid, annotation)
        lilypad_client.ee.projects.annotations.create(project_uuid=settings.project_id, request=request)

    def assign(self, *email: str) -> None:
        """Assign the trace to a user by email."""
        if not email:
            raise ValueError("At least one email address must be provided")

        settings = get_settings()
        lilypad_client = get_sync_client(api_key=settings.api_key)
        span_uuid = self._get_span_uuid(lilypad_client)

        if span_uuid is None:
            from lilypad.exceptions import SpanNotFoundError

            raise SpanNotFoundError(f"Cannot assign: span not found for function {self.function_uuid}")

        lilypad_client.ee.projects.annotations.create(
            project_uuid=settings.project_id,
            request=[
                AnnotationCreate(
                    assignee_email=list(email),
                    function_uuid=self.function_uuid,
                    project_uuid=settings.project_id,
                    span_uuid=span_uuid,
                )
            ],
        )

    def tag(self, *tags: str) -> None:
        """
        Annotate the trace with the given tags.
        """
        if not tags:
            return None
        tag_list = list(tags)
        settings = get_settings()
        client = get_sync_client(api_key=settings.api_key)
        span_uuid = self._get_span_uuid(client)

        if span_uuid is None:  # pragma: no cover
            from lilypad.exceptions import SpanNotFoundError

            raise SpanNotFoundError(f"Cannot tag: span not found for function {self.function_uuid}")

        client.spans.update(span_uuid=span_uuid, tags_by_name=tag_list)
        return None


class AsyncTrace(_TraceBase[_T]):
    """
    A simple trace wrapper that holds the original function's response and allows annotating the trace.
    """

    async def _get_span_uuid(self, client: AsyncLilypad) -> str | None:
        if not self._flush:  # pragma: no cover
            self._force_flush()
        response = await client.projects.functions.spans.list_paginated(
            project_uuid=get_settings().project_id, function_uuid=self.function_uuid
        )
        for span in response.items:  # pragma: no cover
            if span.span_id == self.formated_span_id:
                return span.uuid_
        return None  # pragma: no cover

    async def annotate(self, *annotation: Annotation) -> None:
        """
        Annotate the trace with the given annotation.
        """
        if not annotation:  # pragma: no cover
            raise ValueError("At least one annotation must be provided")

        settings = get_settings()
        lilypad_client = get_async_client(api_key=settings.api_key)
        span_uuid = await self._get_span_uuid(lilypad_client)

        if span_uuid is None:  # pragma: no cover
            from lilypad.exceptions import SpanNotFoundError

            raise SpanNotFoundError(f"Cannot annotate: span not found for function {self.function_uuid}")

        request = self._create_request(settings.project_id, span_uuid, annotation)
        await lilypad_client.ee.projects.annotations.create(project_uuid=settings.project_id, request=request)

    async def assign(self, *email: str) -> None:
        """Assign the trace to a user by email."""
        if not email:  # pragma: no cover
            raise ValueError("At least one email address must be provided")

        settings = get_settings()
        async_client = get_async_client(api_key=settings.api_key)
        span_uuid = await self._get_span_uuid(async_client)

        if span_uuid is None:  # pragma: no cover
            from lilypad.exceptions import SpanNotFoundError

            raise SpanNotFoundError(f"Cannot assign: span not found for function {self.function_uuid}")

        # TODO: update migrate fern client
        await async_client.ee.projects.annotations.create(
            project_uuid=settings.project_id,
            request=[
                AnnotationCreate(
                    assignee_email=list(email),
                    function_uuid=self.function_uuid,
                    project_uuid=settings.project_id,
                    span_uuid=span_uuid,
                )
            ],
        )

    async def tag(self, *tags: str) -> None:
        """
        Annotate the trace with the given tags.
        """
        if not tags:  # pragma: no cover
            return None
        tag_list = list(tags)
        settings = get_settings()
        client = get_async_client(api_key=settings.api_key)
        span_uuid = await self._get_span_uuid(client)

        if span_uuid is None:  # pragma: no cover
            from lilypad.exceptions import SpanNotFoundError

            raise SpanNotFoundError(f"Cannot tag: span not found for function {self.function_uuid}")

        await client.spans.update(span_uuid=span_uuid, tags_by_name=tag_list)
        return None


class NoOpTrace(Generic[_T]):
    """
    A no-op trace wrapper that returns the response when Lilypad is not configured.
    """

    def __init__(self, response: _T) -> None:
        self.response: _T = response

    def annotate(self, *annotation: Annotation) -> None:
        """No-op annotate method."""
        if not annotation:
            raise ValueError("At least one annotation must be provided")

    def assign(self, *email: str) -> None:
        """No-op assign method."""
        ...

    def tag(self, *tags: str) -> None:
        """No-op tag method."""
        ...


class NoOpAsyncTrace(Generic[_T]):
    """
    A no-op async trace wrapper that returns the response when Lilypad is not configured.
    """

    def __init__(self, response: _T) -> None:
        self.response: _T = response

    async def annotate(self, *annotation: Annotation) -> None:
        """No-op annotate method."""
        if not annotation:
            raise ValueError("At least one annotation must be provided")

    async def assign(self, *email: str) -> None:
        """No-op assign method."""
        ...

    async def tag(self, *tags: str) -> None:
        """No-op tag method."""
        ...


# Type definitions for decorator registry
FunctionInfo: TypeAlias = tuple[
    str, str, int, str, dict[str, Any]
]  # (file_path, function_name, line_number, module_name, context)
DecoratorRegistry: TypeAlias = dict[str, list[FunctionInfo]]

# Globals for decorator registry
_RECORDING_ENABLED: bool = False
_DECORATOR_REGISTRY: DecoratorRegistry = {}  # Maps decorator names to lists of function info


def enable_recording() -> None:
    """Enable recording of decorated functions."""
    global _RECORDING_ENABLED
    _RECORDING_ENABLED = True


def disable_recording() -> None:
    """Disable recording of decorated functions."""
    global _RECORDING_ENABLED
    _RECORDING_ENABLED = False


def clear_registry() -> None:
    """Clear the registry of decorated functions."""
    global _DECORATOR_REGISTRY
    _DECORATOR_REGISTRY = {}


DecoratorArgs: TypeAlias = dict[str, Any]
FunctionInfo: TypeAlias = tuple[str, str, int, str, DecoratorArgs]


def _register_decorated_function(
    decorator_name: str, fn: Callable[..., Any], function_name: str, context: dict[str, Any] | None = None
) -> None:
    """Register a function that has been decorated.

    Args:
        decorator_name: The name of the decorator
        fn: The decorated function
        function_name: The name of the function
        context: Optional context information to store with the function
    """
    if not _RECORDING_ENABLED:
        return

    try:
        # Get function information
        file_path: str = inspect.getfile(fn)
        abs_path: str = os.path.abspath(file_path)
        lineno: int = inspect.getsourcelines(fn)[1]
        module_name: str = fn.__module__

        # Add to registry
        if decorator_name not in _DECORATOR_REGISTRY:
            _DECORATOR_REGISTRY[decorator_name] = []

        # Store (file_path, function_name, line_number, module_name)
        _DECORATOR_REGISTRY[decorator_name].append((abs_path, function_name, lineno, module_name, context))
    except (TypeError, OSError):
        # Handle cases where inspect might fail (e.g., built-in functions)
        pass


def get_decorated_functions(decorator_name: str | None = None) -> DecoratorRegistry:
    """Get information about registered decorated functions.

    Args:
        decorator_name: Optional name of decorator to filter by

    Returns:
        Dictionary mapping decorator names to lists of function information tuples
    """
    if decorator_name:
        return {decorator_name: _DECORATOR_REGISTRY.get(decorator_name, [])}
    return _DECORATOR_REGISTRY.copy()


class SyncVersionedFunction(Protocol[_P, _R_CO]):
    """Protocol for the `VersionedFunction` decorator return type."""

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R_CO:
        """Protocol for the `VersionFunction` decorator return type."""
        ...

    def version(
        self,
        forced_version: int,
        sandbox_runner: SandboxRunner | None = None,
    ) -> Callable[_P, _R_CO]:
        """Protocol for the `VersionFunction` decorator return type."""
        ...

    def remote(
        self,
        sandbox_runner: SandboxRunner | None = None,
    ) -> _R_CO:
        """Protocol for the `VersionFunction` decorator return type."""
        ...


class AsyncVersionedFunction(Protocol[_P, _R_CO]):
    """Protocol for the `VersionFunction` decorator return type."""

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> Coroutine[Any, Any, _R_CO]:
        """Protocol for the `VersionFunction` decorator return type."""
        ...

    def version(
        self,
        forced_version: int,
        sandbox_runner: SandboxRunner | None = None,
    ) -> Coroutine[Any, Any, Callable[_P, _R_CO]]:
        """Protocol for the `VersionFunction` decorator return type."""
        ...

    def remote(
        self,
        sandbox_runner: SandboxRunner | None = None,
    ) -> Coroutine[Any, Any, _R_CO]:
        """Protocol for the `VersionFunction` decorator return type."""
        ...


class TraceDecoratedFunctionWithContext(Protocol[_P, _R]):
    """Protocol for the `VersioningDecorator` decorator return type."""

    def __call__(self, trace_ctx: Span, *args: _P.args, **kwargs: _P.kwargs) -> _R: ...


class TraceDecorator(Protocol):
    """Protocol for the `VersioningDecorator` decorator return type."""

    @overload
    def __call__(
        self, fn: TraceDecoratedFunctionWithContext[_P, Coroutine[Any, Any, _R]]
    ) -> Callable[_P, Coroutine[Any, Any, _R]]: ...

    @overload
    def __call__(self, fn: TraceDecoratedFunctionWithContext[_P, _R]) -> Callable[_P, _R]: ...

    @overload
    def __call__(self, fn: Callable[_P, Coroutine[Any, Any, _R]]) -> Callable[_P, Coroutine[Any, Any, _R]]: ...

    @overload
    def __call__(self, fn: Callable[_P, _R]) -> Callable[_P, _R]: ...

    def __call__(
        self,
        fn: TraceDecoratedFunctionWithContext[_P, Coroutine[Any, Any, _R]]
        | TraceDecoratedFunctionWithContext[_P, _R]
        | Callable[_P, _R]
        | Callable[_P, Coroutine[Any, Any, _R]],
    ) -> Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]:
        """Protocol `call` definition for `VersioningDecorator` decorator return type."""
        ...


class WrappedTraceDecorator(Protocol):
    """Protocol for the `WrappedTraceDecorator` decorator return type."""

    @overload
    def __call__(
        self, fn: TraceDecoratedFunctionWithContext[_P, Coroutine[Any, Any, _R]]
    ) -> Callable[_P, Coroutine[Any, Any, Trace[_R]]]: ...

    @overload
    def __call__(self, fn: TraceDecoratedFunctionWithContext[_P, _R]) -> Callable[_P, Trace[_R]]: ...

    @overload
    def __call__(self, fn: Callable[_P, Coroutine[Any, Any, _R]]) -> Callable[_P, Coroutine[Any, Any, Trace[_R]]]: ...

    @overload
    def __call__(self, fn: Callable[_P, _R]) -> Callable[_P, Trace[_R]]: ...

    def __call__(
        self,
        fn: TraceDecoratedFunctionWithContext[_P, Coroutine[Any, Any, _R]]
        | TraceDecoratedFunctionWithContext[_P, _R]
        | Callable[_P, _R]
        | Callable[_P, Coroutine[Any, Any, _R]],
    ) -> Callable[_P, Trace[_R]] | Callable[_P, Coroutine[Any, Any, Trace[_R]]]:
        """Protocol `call` definition for `VersioningDecorator` decorator return type."""
        ...


class VersionedFunctionTraceDecorator(Protocol):
    """Protocol for the `VersionedFunction` decorator return type."""

    @overload
    def __call__(
        self, fn: TraceDecoratedFunctionWithContext[_P, Coroutine[Any, Any, _R]]
    ) -> AsyncVersionedFunction[_P, _R]: ...

    @overload
    def __call__(self, fn: TraceDecoratedFunctionWithContext[_P, _R]) -> SyncVersionedFunction[_P, _R]: ...

    @overload
    def __call__(self, fn: Callable[_P, Coroutine[Any, Any, _R]]) -> AsyncVersionedFunction[_P, _R]: ...

    @overload
    def __call__(self, fn: Callable[_P, _R]) -> SyncVersionedFunction[_P, _R]: ...

    def __call__(
        self,
        fn: TraceDecoratedFunctionWithContext[_P, Coroutine[Any, Any, _R]]
        | TraceDecoratedFunctionWithContext[_P, _R]
        | Callable[_P, _R]
        | Callable[_P, Coroutine[Any, Any, _R]],
    ) -> AsyncVersionedFunction[_P, _R] | SyncVersionedFunction[_P, _R]:
        """Protocol `call` definition for `VersionedFunction` decorator return type."""
        ...


class WrappedVersionedFunctionTraceDecorator(Protocol):
    """Protocol for the `WrappedVersionedFunctionTraceDecorator` decorator return type."""

    @overload
    def __call__(
        self, fn: TraceDecoratedFunctionWithContext[_P, Coroutine[Any, Any, _R]]
    ) -> AsyncVersionedFunction[_P, Trace[_R]]: ...

    @overload
    def __call__(self, fn: TraceDecoratedFunctionWithContext[_P, _R]) -> SyncVersionedFunction[_P, Trace[_R]]: ...

    @overload
    def __call__(self, fn: Callable[_P, Coroutine[Any, Any, _R]]) -> AsyncVersionedFunction[_P, Trace[_R]]: ...

    @overload
    def __call__(self, fn: Callable[_P, _R]) -> SyncVersionedFunction[_P, Trace[_R]]: ...

    def __call__(
        self,
        fn: TraceDecoratedFunctionWithContext[_P, Coroutine[Any, Any, _R]]
        | TraceDecoratedFunctionWithContext[_P, _R]
        | Callable[_P, _R]
        | Callable[_P, Coroutine[Any, Any, _R]],
    ) -> AsyncVersionedFunction[_P, Trace[_R]] | SyncVersionedFunction[_P, Trace[_R]]:
        """Protocol `call` definition for `VersionedFunction` decorator return type."""
        ...


_TraceAttribute: TypeAlias = dict[str, AttributeValue]


class _ResultHolder:
    """A class to hold the result of a function call."""

    def __init__(self) -> None:
        self.result = None

    def set_result(self, result: Any) -> None:
        """Set the result attribute."""
        self.result: Any = result


_trace_context: ContextVar[MappingProxyType] = ContextVar("_trace_context", default=MappingProxyType({}))


def _get_trace_context() -> dict[str, Any]:
    return dict(_trace_context.get())


def _set_trace_context(trace_ctx: dict[str, Any]) -> None:
    _trace_context.set(MappingProxyType(trace_ctx.copy()))


@contextmanager
def _set_span_attributes(
    span: Span,
    span_attribute: _TraceAttribute,
    is_async: bool,
    function: FunctionPublic | None,
    decorator_tags: list[str] | None = None,
    serializers: SerializerMap | None = None,
) -> Generator[_ResultHolder, None, None]:
    """Set the attributes on the span."""
    if span.opentelemetry_span is None:
        result_holder = _ResultHolder()
        yield result_holder
        return
    settings = get_settings()
    span_attribute["lilypad.project_uuid"] = settings.project_id if settings.project_id else ""
    span_attribute["lilypad.type"] = trace_type = _get_trace_type(function)
    span_attribute["lilypad.is_async"] = is_async
    if decorator_tags is not None:
        span_attribute["lilypad.trace.tags"] = decorator_tags
    if function:
        function_uuid = function.uuid_
        span_attribute[f"lilypad.{trace_type}.signature"] = function.signature
        span_attribute[f"lilypad.{trace_type}.code"] = function.code
    else:
        function_uuid = ""
    span_attribute["lilypad.function.uuid"] = function_uuid
    span.opentelemetry_span.set_attributes(span_attribute)
    result_holder = _ResultHolder()
    yield result_holder
    original_output = result_holder.result
    span.opentelemetry_span.set_attribute(
        f"lilypad.{trace_type}.output", "" if original_output is None else to_text(original_output, serializers)
    )


def _construct_trace_attributes(
    trace_type: str,
    arg_types: dict[str, str],
    arg_values: dict[str, Any],
    serializers: SerializerMap,
) -> dict[str, AttributeValue]:
    jsonable_arg_values = {}
    for arg_name, arg_value in arg_values.items():
        try:
            serialized_arg_value = fast_jsonable(arg_value, custom_serializers=serializers)
        except (TypeError, ValueError, orjson.JSONEncodeError):  # pragma: no cover
            serialized_arg_value = "could not serialize"
        jsonable_arg_values[arg_name] = serialized_arg_value
    return {
        f"lilypad.{trace_type}.arg_types": json_dumps(arg_types),
        f"lilypad.{trace_type}.arg_values": json_dumps(jsonable_arg_values),
    }


_SANDBOX_CUSTOM_RESULT = {
    "result": "result",
    "trace_context": "_get_trace_context()",
}
_SANDBOX_PRE_ACTIONS = [
    "lilypad.configure(log_handlers=[logging.StreamHandler(sys.stderr)])",
]
_SANDBOX_AFTER_ACTIONS = [
    "result = result.response if isinstance(result, AsyncTrace | Trace) else result",
    "with suppress(ImportError): from mirascope.core import BaseCallResponse",
    "result = getattr(result, 'content', result) if (mirascope_response := locals().get('BaseCallResponse')) else result",
]
_SANDBOX_EXTRA_IMPORT = [
    f"from {TRACE_MODULE_NAME} import _get_trace_context, AsyncTrace, Trace",
    "import lilypad",
    "import sys",
    "import logging",
    "from contextlib import suppress",
]


@overload
def trace(
    name: str | None = None,
    *,
    versioning: None = None,
    mode: None = None,
    tags: list[str] | None = None,
    serializers: SerializerMap | None = None,
) -> TraceDecorator: ...


@overload
def trace(
    name: str | None = None,
    *,
    versioning: Literal["automatic"],
    mode: None = None,
    tags: list[str] | None = None,
    serializers: SerializerMap | None = None,
) -> VersionedFunctionTraceDecorator: ...


@overload
def trace(
    name: str | None = None,
    *,
    versioning: None,
    mode: Literal["wrap"],
    tags: list[str] | None = None,
    serializers: SerializerMap | None = None,
) -> WrappedTraceDecorator: ...


@overload
def trace(
    name: str | None = None,
    *,
    versioning: Literal["automatic"],
    mode: Literal["wrap"],
    tags: list[str] | None = None,
    serializers: SerializerMap | None = None,
) -> WrappedVersionedFunctionTraceDecorator: ...


def trace(
    name: str | None = None,
    *,
    versioning: Literal["automatic"] | None = None,
    mode: Literal["wrap"] | None = None,
    tags: list[str] | None = None,
    serializers: SerializerMap | None = None,
) -> TraceDecorator | VersionedFunctionTraceDecorator:
    """Decorator for tracing function execution with distributed tracing support.

    This decorator instruments functions to create OpenTelemetry spans, enabling
    distributed tracing across service boundaries. It supports automatic context
    propagation for maintaining trace continuity in microservices architectures.

    Args:
        name: Optional custom name for the span. If None, uses the function's
              qualified name.
        versioning: If "automatic", enables function versioning to track code changes.
        mode: If "wrap", returns a Trace object with the response and annotation methods.
        tags: List of tags to attach to spans created by this function.
        serializers: Custom serializers for function arguments and return values.

    Returns:
        A decorator that instruments the function with tracing capabilities.

    Example:
        Basic usage:

        ```python
        from lilypad import trace


        @trace()
        def process_data(data: dict) -> dict:
            # Function is automatically traced
            result = {"processed": True, "count": len(data)}
            return result


        # When called, creates a span with timing and metadata
        result = process_data({"items": [1, 2, 3]})
        ```

        Distributed tracing with HTTP services:

        ```python
        from fastapi import FastAPI, Request
        from lilypad import trace, propagated_context

        app = FastAPI()


        @trace()
        def process_request(data: dict) -> dict:
            # This function is defined at module level
            result = heavy_processing(data)
            return {"status": "success", "result": result}


        @app.post("/process")
        async def api_endpoint(request: Request, data: dict):
            # Use context manager to propagate trace context
            with propagated_context(extract_from=dict(request.headers)):
                # process_request will be a child of the incoming trace
                return await process_request(data)
        ```

        Using with explicit parent context:

        ```python
        from opentelemetry import context as otel_context
        from lilypad import trace, propagated_context
        import threading


        @trace()
        def process_in_thread(data: dict):
            # This function is defined at module level
            return transform_data(data)


        # In main thread
        @trace()
        def main_process(data: dict):
            # Capture current context
            current_ctx = otel_context.get_current()

            # Pass to worker thread
            thread = threading.Thread(target=worker_process, args=(data, current_ctx))
            thread.start()


        # In worker thread
        def worker_process(data: dict, parent_ctx):
            # Use context manager for parent context
            with propagated_context(parent=parent_ctx):
                # This span is a child of main_process span
                return process_in_thread(data)
        ```

        With versioning and tags:

        ```python
        @trace(versioning="automatic", tags=["production", "critical"], mode="wrap")
        def ml_inference(input_data: dict) -> dict:
            prediction = model.predict(input_data)
            return {"prediction": prediction, "confidence": 0.95}


        # Returns a Trace object
        result = ml_inference({"features": [1, 2, 3]})
        print(result.response)  # Access the actual result
        result.annotate(...)  # Add annotations to the trace
        ```

    Note:
        - For distributed tracing, use the `propagated_context` context manager with `extract_from` parameter
        - Context extraction supports multiple propagation formats (W3C, B3, Jaeger)
        - Configure propagation format using `lilypad.configure(propagator="...")`
    """
    decorator_tags = sorted(set(tags)) if tags else None

    @overload
    def decorator(
        fn: TraceDecoratedFunctionWithContext[_P, Coroutine[Any, Any, _R]],
    ) -> Callable[_P, Coroutine[Any, Any, _R]]: ...

    @overload
    def decorator(fn: TraceDecoratedFunctionWithContext[_P, _R]) -> Callable[_P, _R]: ...

    @overload
    def decorator(fn: Callable[_P, Coroutine[Any, Any, _R]]) -> Callable[_P, Coroutine[Any, Any, _R]]: ...

    @overload
    def decorator(fn: Callable[_P, _R]) -> Callable[_P, _R]: ...

    def decorator(
        fn: TraceDecoratedFunctionWithContext[_P, Coroutine[Any, Any, _R]]
        | TraceDecoratedFunctionWithContext[_P, _R]
        | Callable[_P, _R]
        | Callable[_P, Coroutine[Any, Any, _R]],
    ) -> Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]:
        is_mirascope_call = hasattr(fn, "__mirascope_call__")
        prompt_template = (
            fn._prompt_template if hasattr(fn, "_prompt_template") else ""  # pyright: ignore[reportFunctionMemberAccess]
        )

        if _RECORDING_ENABLED and versioning == "automatic":
            _register_decorated_function(
                TRACE_MODULE_NAME, fn, Closure.from_fn(fn).name, {"mode": mode, "tags": decorator_tags}
            )

        local_serializers = serializers or {}

        settings = get_settings()

        signature = get_signature(fn)

        trace_name = get_qualified_name(fn) if name is None else name
        if fn_is_async(fn):

            async def execute_user_function_only(*args: _P.args, **kwargs: _P.kwargs) -> _R:  # pragma: no cover
                """Fallback: execute only the user function without any API interactions."""
                return await fn(*args, **kwargs)

            @call_safely(execute_user_function_only)
            @wraps(fn)
            async def inner_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                if not isinstance(get_tracer_provider(), TracerProvider):
                    global _trace_warning_shown
                    with _trace_warning_lock:
                        if not _trace_warning_shown:
                            logger.warning(
                                "Lilypad has not been configured. @trace decorator is disabled "
                                "for function '%s'. Call `lilypad.configure(...)` early in program start-up.",
                                trace_name,
                            )
                            _trace_warning_shown = True

                    output = await fn(*args, **kwargs)
                    if mode == "wrap":
                        # Return a no-op AsyncTrace object
                        return NoOpAsyncTrace(response=output)
                    return output

                with Span(trace_name) as span:
                    final_args = args
                    final_kwargs = kwargs
                    needs_trace_ctx = "trace_ctx" in signature.parameters
                    has_user_provided_trace_ctx = False
                    try:
                        bound_call_args = signature.bind(*args, **kwargs)
                        has_user_provided_trace_ctx = "trace_ctx" in bound_call_args.arguments
                    except TypeError:
                        pass
                    if needs_trace_ctx and not has_user_provided_trace_ctx:
                        final_args = (span, *args)

                    # If span is in no-op mode, just execute the function with proper args
                    if span.is_noop:
                        output = await fn(*final_args, **final_kwargs)
                        if mode == "wrap":
                            return NoOpAsyncTrace(response=output)
                        return output
                    arg_types, arg_values = inspect_arguments(fn, *final_args, **final_kwargs)
                    arg_values.pop("trace_ctx", None)
                    arg_types.pop("trace_ctx", None)

                    async_lilypad_client = get_async_client(api_key=settings.api_key)

                    closure = Closure.from_fn(fn)

                    async def get_or_create_function_async() -> FunctionPublic | None:
                        try:
                            return await get_function_by_hash_async(
                                project_uuid=settings.project_id, function_hash=closure.hash
                            )
                        except NotFoundError:
                            return await async_lilypad_client.projects.functions.create(
                                project_uuid_=settings.project_id,
                                project_uuid=settings.project_id,
                                code=closure.code,
                                hash=closure.hash,
                                name=closure.name,
                                signature=closure.signature,
                                arg_types=arg_types,
                                dependencies=closure.dependencies,
                                is_versioned=True,
                                prompt_template=prompt_template,
                            )

                    if versioning == "automatic":
                        try:
                            function = await get_or_create_function_async()
                        except (httpx.NetworkError, httpx.TimeoutException, OSError) as exc:
                            logger.error(
                                "Failed to connect to Lilypad server for versioning: %s. "
                                "Continuing without versioning. LLM calls will still work.",
                                exc,
                            )
                            function = None
                        except LilypadException as exc:
                            logger.debug("Lilypad API error during versioning: %s. Continuing without versioning.", exc)
                            function = None
                    else:
                        function = None

                    function_uuid = function.uuid_ if function else None

                    trace_attribute = _construct_trace_attributes(
                        trace_type=_get_trace_type(function),
                        arg_types=arg_types,
                        arg_values=arg_values,
                        serializers=local_serializers,
                    )

                    if is_mirascope_call:  # pragma: no cover
                        decorator_inner = create_mirascope_middleware(
                            function,
                            arg_types,
                            arg_values,
                            True,
                            prompt_template,
                            settings.project_id,
                            current_span=span.opentelemetry_span,
                        )
                        output = await decorator_inner(fn)(*final_args, **final_kwargs)
                    else:
                        with _set_span_attributes(
                            span, trace_attribute, is_async=True, function=function, serializers=local_serializers
                        ) as result_holder:
                            output = await fn(*final_args, **final_kwargs)
                            result_holder.set_result(output)
                    span_id = span.span_id
                    _set_trace_context({"span_id": span_id, "function_uuid": function_uuid})

                if mode == "wrap":
                    return AsyncTrace(response=output, span_id=span_id, function_uuid=function_uuid)
                return output  # pyright: ignore [reportReturnType]

            if versioning is None:
                return inner_async

            function_name = get_qualified_name(fn)

            async def _specific_function_version_async(
                forced_version: int,
                sandbox: SandboxRunner | None = None,
            ) -> Callable[_P, _R]:
                try:
                    versioned_function = await get_function_by_version_async(
                        version_num=forced_version,
                        project_uuid=settings.project_id,
                        function_name=function_name,
                    )
                    versioned_function_closure = get_cached_closure(versioned_function)
                except Exception as e:  # pragma: no cover
                    raise RemoteFunctionError(f"Failed to retrieve function {fn.__name__}: {e}")

                if sandbox is None:
                    sandbox = SubprocessSandboxRunner(os.environ.copy())

                @wraps(fn)
                def _inner_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                    result = sandbox.execute_function(
                        versioned_function_closure,
                        *args,
                        custom_result=_SANDBOX_CUSTOM_RESULT,
                        pre_actions=_SANDBOX_PRE_ACTIONS,
                        after_actions=_SANDBOX_AFTER_ACTIONS,
                        extra_imports=_SANDBOX_EXTRA_IMPORT,
                        **kwargs,
                    )
                    if mode == "wrap":  # pragma: no cover
                        return AsyncTrace(
                            response=result["result"],
                            span_id=result["trace_context"]["span_id"],
                            function_uuid=result["trace_context"]["function_uuid"],
                        )
                    return result["result"]

                return _inner_async

            inner_async.version = _specific_function_version_async  # pyright: ignore [reportAttributeAccessIssue, reportFunctionMemberAccess]

            async def _deployed_version_async(
                *args: _P.args,
                sandbox: SandboxRunner | None = None,
                ttl: float | None = None,
                force_refresh: bool = False,
                **kwargs: _P.kwargs,
            ) -> _R:
                try:
                    deployed_function = await get_deployed_function_async(
                        project_uuid=settings.project_id,
                        ttl=ttl,
                        force_refresh=force_refresh,
                        function_name=function_name,
                    )
                    deployed_function_closure = get_cached_closure(deployed_function)
                except Exception as e:  # pragma: no cover
                    raise RemoteFunctionError(f"Failed to retrieve function {fn.__name__}: {e}")

                if sandbox is None:
                    sandbox = SubprocessSandboxRunner(os.environ.copy())

                result = sandbox.execute_function(
                    deployed_function_closure,
                    *args,
                    custom_result=_SANDBOX_CUSTOM_RESULT,
                    pre_actions=_SANDBOX_PRE_ACTIONS,
                    after_actions=_SANDBOX_AFTER_ACTIONS,
                    extra_imports=_SANDBOX_EXTRA_IMPORT,
                    **kwargs,
                )
                if mode == "wrap":
                    return AsyncTrace(
                        response=result["result"],
                        span_id=result["trace_context"]["span_id"],
                        function_uuid=result["trace_context"]["function_uuid"],
                    )
                return result["result"]

            inner_async.remote = _deployed_version_async
            return inner_async
        else:

            def execute_user_function_only(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                """Fallback: execute only the user function without any API interactions."""
                return fn(*args, **kwargs)  # pragma: no cover

            @call_safely(execute_user_function_only)
            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                if not isinstance(get_tracer_provider(), TracerProvider):
                    global _trace_warning_shown
                    with _trace_warning_lock:
                        if not _trace_warning_shown:
                            logger.warning(
                                "Lilypad has not been configured. @trace decorator is disabled "
                                "for function '%s'. Call `lilypad.configure(...)` early in program start-up.",
                                trace_name,
                            )
                            _trace_warning_shown = True

                    output = fn(*args, **kwargs)
                    if mode == "wrap":
                        # Return a no-op Trace object
                        return NoOpTrace(response=output)
                    return output

                with Span(trace_name) as span:
                    final_args = args
                    final_kwargs = kwargs
                    needs_trace_ctx = "trace_ctx" in signature.parameters
                    has_user_provided_trace_ctx = False
                    try:
                        bound_call_args = signature.bind(*args, **kwargs)
                        has_user_provided_trace_ctx = "trace_ctx" in bound_call_args.arguments
                    except TypeError:
                        pass

                    if needs_trace_ctx and not has_user_provided_trace_ctx:
                        final_args = (span, *args)

                    # If span is in no-op mode, just execute the function with proper args
                    if span.is_noop:
                        output = fn(*final_args, **final_kwargs)
                        if mode == "wrap":
                            return NoOpTrace(response=output)
                        return output
                    arg_types, arg_values = inspect_arguments(fn, *final_args, **final_kwargs)
                    arg_values.pop("trace_ctx", None)
                    arg_types.pop("trace_ctx", None)

                    lilypad_client = get_sync_client(api_key=settings.api_key)

                    closure = Closure.from_fn(fn)

                    def get_or_create_function_sync() -> FunctionPublic | None:
                        try:
                            return get_function_by_hash_sync(
                                project_uuid=settings.project_id, function_hash=closure.hash
                            )
                        except NotFoundError:
                            return lilypad_client.projects.functions.create(
                                project_uuid_=settings.project_id,
                                project_uuid=settings.project_id,
                                code=closure.code,
                                hash=closure.hash,
                                name=closure.name,
                                signature=closure.signature,
                                arg_types=arg_types,
                                dependencies=closure.dependencies,
                                is_versioned=True,
                                prompt_template=prompt_template,
                            )

                    if versioning == "automatic":
                        try:
                            function = get_or_create_function_sync()
                        except (httpx.NetworkError, httpx.TimeoutException, OSError) as exc:
                            logger.error(
                                "Failed to connect to Lilypad server for versioning: %s. "
                                "Continuing without versioning. LLM calls will still work.",
                                exc,
                            )
                            function = None
                        except LilypadException as exc:
                            logger.debug("Lilypad API error during versioning: %s. Continuing without versioning.", exc)
                            function = None
                    else:
                        function = None

                    function_uuid = function.uuid_ if function else None

                    trace_attribute = _construct_trace_attributes(
                        trace_type=_get_trace_type(function),
                        arg_types=arg_types,
                        arg_values=arg_values,
                        serializers=local_serializers,
                    )

                    if is_mirascope_call:
                        decorator_inner = create_mirascope_middleware(
                            function,
                            arg_types,
                            arg_values,
                            False,
                            prompt_template,
                            settings.project_id,
                            current_span=span.opentelemetry_span,
                            decorator_tags=decorator_tags,
                        )
                        output = decorator_inner(fn)(*final_args, **final_kwargs)
                    else:
                        with _set_span_attributes(
                            span,
                            trace_attribute,
                            is_async=False,
                            function=function,
                            decorator_tags=decorator_tags,
                            serializers=local_serializers,
                        ) as result_holder:
                            output = fn(*final_args, **final_kwargs)
                            result_holder.set_result(output)
                    span_id = span.span_id
                    _set_trace_context({"span_id": span_id, "function_uuid": function_uuid})

                if mode == "wrap":
                    return Trace(response=output, span_id=span_id, function_uuid=function_uuid)
                return output  # pyright: ignore [reportReturnType]

            if versioning is None:
                return inner  # pyright: ignore [reportReturnType]

            function_name = get_qualified_name(fn)

            def _specific_function_version(
                forced_version: int,
                sandbox: SandboxRunner | None = None,
            ) -> Callable[_P, _R]:
                try:
                    versioned_function = get_function_by_version_sync(
                        version_num=forced_version,
                        project_uuid=settings.project_id,
                        function_name=function_name,
                    )
                    versioned_function_closure = get_cached_closure(versioned_function)
                except Exception as e:  # pragma: no cover
                    raise RemoteFunctionError(f"Failed to retrieve function {fn.__name__}: {e}")

                if sandbox is None:
                    sandbox = SubprocessSandboxRunner(os.environ.copy())

                @wraps(fn)
                def _inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                    result = sandbox.execute_function(
                        versioned_function_closure,
                        *args,
                        custom_result=_SANDBOX_CUSTOM_RESULT,
                        pre_actions=_SANDBOX_PRE_ACTIONS,
                        after_actions=_SANDBOX_AFTER_ACTIONS,
                        extra_imports=_SANDBOX_EXTRA_IMPORT,
                        **kwargs,
                    )
                    if mode == "wrap":
                        return Trace(
                            response=result["result"],
                            span_id=result["trace_context"]["span_id"],
                            function_uuid=result["trace_context"]["function_uuid"],
                        )
                    return result["result"]

                return _inner

            inner.version = _specific_function_version  # pyright: ignore [reportAttributeAccessIssue, reportFunctionMemberAccess]

            def _deployed_version(
                *args: _P.args,
                sandbox: SandboxRunner | None = None,
                ttl: float | None = None,
                force_refresh: bool = False,
                **kwargs: _P.kwargs,
            ) -> _R:
                try:
                    deployed_function = get_deployed_function_sync(
                        project_uuid=settings.project_id,
                        ttl=ttl,
                        force_refresh=force_refresh,
                        function_name=function_name,
                    )
                    deployed_function_closure = get_cached_closure(deployed_function)
                except Exception as e:  # pragma: no cover
                    raise RemoteFunctionError(f"Failed to retrieve function {fn.__name__}: {e}")

                if sandbox is None:
                    sandbox = SubprocessSandboxRunner(os.environ.copy())

                result = sandbox.execute_function(
                    deployed_function_closure,
                    *args,
                    custom_result=_SANDBOX_CUSTOM_RESULT,
                    pre_actions=_SANDBOX_PRE_ACTIONS,
                    after_actions=_SANDBOX_AFTER_ACTIONS,
                    extra_imports=_SANDBOX_EXTRA_IMPORT,
                    **kwargs,
                )
                if mode == "wrap":
                    return Trace(
                        response=result["result"],
                        span_id=result["trace_context"]["span_id"],
                        function_uuid=result["trace_context"]["function_uuid"],
                    )
                return result["result"]

            inner.remote = _deployed_version
            return inner

    return decorator
