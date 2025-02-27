"""The `generations` module for automatically versioning and tracing LLM generations."""

import inspect
import json
import threading
import typing
from collections.abc import Callable, Coroutine, Generator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from functools import wraps
from typing import Any, Literal, ParamSpec, Protocol, TypeVar, overload

from fastapi.encoders import jsonable_encoder
from mirascope import llm
from mirascope.core import prompt_template
from mirascope.core.base._utils import fn_is_async
from mirascope.llm.call_response import CallResponse
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Span, get_tracer, get_tracer_provider
from opentelemetry.util.types import AttributeValue
from pydantic import BaseModel

from ._utils import (
    Closure,
    call_safely,
    create_mirascope_middleware,
    get_qualified_name,
    inspect_arguments,
    load_config,
)
from .messages import Message
from .response_models import _create_model_from_json_schema
from .server.client import LilypadClient, LilypadNotFoundError
from .server.schemas import GenerationPublic
from .server.settings import get_settings
from .stream import Stream

_P = ParamSpec("_P")
_R = TypeVar("_R")
_R_CO = TypeVar("_R_CO", covariant=True)


current_generation: ContextVar[GenerationPublic | None] = ContextVar(
    "current_generation", default=None
)


class SyncGenerationFunction(Protocol[_P, _R_CO]):
    """Protocol for the `generation` decorator return type."""

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R_CO:
        """Protocol for the `generation` decorator return type."""
        ...

    def version(self, forced_version: int) -> Callable[_P, _R_CO]:
        """Protocol for the `generation` decorator return type."""
        ...


class AsyncGenerationFunction(Protocol[_P, _R_CO]):
    """Protocol for the `generation` decorator return type."""

    def __call__(
        self, *args: _P.args, **kwargs: _P.kwargs
    ) -> Coroutine[Any, Any, _R_CO]:
        """Protocol for the `generation` decorator return type."""
        ...

    def version(
        self, forced_version: int
    ) -> Coroutine[Any, Any, Callable[_P, Coroutine[Any, Any, _R_CO]]]:
        """Protocol for the `generation` decorator return type."""
        ...


class GenerationVersioningDecorator(Protocol):
    """Protocol for the `generation` decorator return type."""

    @overload
    def __call__(  # pyright: ignore [reportOverlappingOverload]
        self, fn: Callable[_P, Coroutine[Any, Any, _R]]
    ) -> AsyncGenerationFunction[_P, _R]: ...

    @overload
    def __call__(self, fn: Callable[_P, _R]) -> SyncGenerationFunction[_P, _R]: ...

    def __call__(
        self, fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]
    ) -> SyncGenerationFunction[_P, _R] | AsyncGenerationFunction[_P, _R]:
        """Protocol `call` definition for `generation` decorator return type."""
        ...


class ManagedGenerationVersioningDecorator(Protocol):
    """Protocol for the `generation` decorator return type."""

    @overload
    def __call__(  # pyright: ignore [reportOverlappingOverload]
        self, fn: Callable[_P, Coroutine[Any, Any, _R]]
    ) -> AsyncGenerationFunction[_P, Message | Stream]: ...

    @overload
    def __call__(
        self, fn: Callable[_P, _R]
    ) -> SyncGenerationFunction[_P, Message | Stream]: ...

    def __call__(
        self, fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]
    ) -> (
        SyncGenerationFunction[_P, Message | Stream]
        | AsyncGenerationFunction[_P, Message | Stream]
    ):
        """Protocol `call` definition for `generation` decorator return type."""
        ...


class GenerationDecorator(Protocol):
    """Protocol for the `generation` decorator return type."""

    @overload
    def __call__(
        self, fn: Callable[_P, Coroutine[Any, Any, _R]]
    ) -> Callable[_P, Coroutine[Any, Any, _R]]: ...

    @overload
    def __call__(self, fn: Callable[_P, _R]) -> Callable[_P, _R]: ...

    def __call__(
        self, fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]
    ) -> Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]:
        """Protocol `call` definition for `generation` decorator return type."""
        ...


def _get_batch_span_processor() -> BatchSpanProcessor | None:
    """Get the BatchSpanProcessor from the current TracerProvider.

    Retrieve the BatchSpanProcessor from the current TracerProvider dynamically.
    This avoids using a global variable by inspecting the provider's _active_span_processors.
    """
    tracer_provider = get_tracer_provider()
    processor = getattr(tracer_provider, "_active_span_processor", None)
    if not processor:
        return None
    _span_processors = getattr(processor, "_span_processors", None)
    if _span_processors:
        for processor in _span_processors:
            if isinstance(processor, BatchSpanProcessor):
                return processor
    return None


@contextmanager
def outermost_lock_context(enable_lock: bool) -> Generator[None, None, None]:
    """Acquire the BatchSpanProcessor's condition lock if enable_lock is True.

    This context manager is intended for use in the outermost generation.
    When enable_lock is True, it retrieves the current BatchSpanProcessor and acquires its
    condition lock. This ensures that flush operations are synchronized and only executed
    at the outermost generation level.
    For inner generations (enable_lock is False), no lock is acquired.
    """
    if not enable_lock:
        yield
        return
    processor = _get_batch_span_processor()
    if not processor:
        yield
        return
    with processor.condition:
        yield


# Global counter and lock for span order.
_span_counter_lock = threading.Lock()
_span_counter = 0


@contextmanager
def span_order_context(span: Span) -> Generator[None, None, None]:
    """Assign an explicit order to a span using a global counter."""
    global _span_counter
    with _span_counter_lock:
        _span_counter += 1
        order = _span_counter
    span.set_attribute("lilypad.span.order", order)
    yield


def _construct_trace_attributes(
    generation: GenerationPublic,
    arg_types: dict[str, str],
    arg_values: dict[str, Any],
    prompt_template: str,
    is_async: bool,
) -> dict[str, AttributeValue]:
    jsonable_arg_values = {}
    settings = get_settings()
    for arg_name, arg_value in arg_values.items():
        try:
            serialized_arg_value = jsonable_encoder(arg_value)
        except ValueError:
            serialized_arg_value = "could not serialize"
        jsonable_arg_values[arg_name] = serialized_arg_value
    return {
        "lilypad.project_uuid": settings.project_id if settings.project_id else "",
        "lilypad.type": "generation",
        "lilypad.generation.uuid": str(generation.uuid),
        "lilypad.generation.name": generation.name,
        "lilypad.generation.signature": generation.signature,
        "lilypad.generation.code": generation.code,
        "lilypad.generation.arg_types": json.dumps(arg_types),
        "lilypad.generation.arg_values": json.dumps(jsonable_arg_values),
        "lilypad.generation.prompt_template": prompt_template,
        "lilypad.generation.version": generation.version_num
        if generation.version_num
        else -1,
        "lilypad.is_async": is_async,
    }


def _trace(
    generation: GenerationPublic,
    arg_types: dict[str, str],
    arg_values: dict[str, Any],
    prompt_template: str = "",
) -> GenerationDecorator:
    @overload
    def decorator(
        fn: Callable[_P, Coroutine[Any, Any, _R]],
    ) -> Callable[_P, Coroutine[Any, Any, _R]]: ...

    @overload
    def decorator(fn: Callable[_P, _R]) -> Callable[_P, _R]: ...

    def decorator(
        fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]],
    ) -> Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]:
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def inner_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                with (
                    get_tracer("lilypad").start_as_current_span(
                        get_qualified_name(fn)
                    ) as span,
                    span_order_context(span),
                ):
                    attributes: dict[str, AttributeValue] = _construct_trace_attributes(
                        generation, arg_types, arg_values, prompt_template, True
                    )
                    span.set_attributes(attributes)
                    output = await fn(*args, **kwargs)
                    if isinstance(output, BaseModel):
                        output = str(output.model_dump())
                    span.set_attribute("lilypad.generation.output", str(output))
                return output  # pyright: ignore [reportReturnType]

            return inner_async

        else:

            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                with (
                    get_tracer("lilypad").start_as_current_span(
                        get_qualified_name(fn)
                    ) as span,
                    span_order_context(span),
                ):
                    attributes: dict[str, AttributeValue] = _construct_trace_attributes(
                        generation, arg_types, arg_values, prompt_template, False
                    )
                    span.set_attributes(attributes)
                    output = fn(*args, **kwargs)
                    if isinstance(output, BaseModel):
                        output = str(output.model_dump())
                    span.set_attribute("lilypad.generation.output", str(output))
                return output  # pyright: ignore [reportReturnType]

            return inner

    return decorator


@overload
def _build_mirascope_call(  # pyright: ignore [reportOverlappingOverload]
    generation_public: GenerationPublic, fn: Callable[_P, Coroutine[Any, Any, _R]]
) -> Callable[_P, Coroutine[Any, Any, Message | Stream]]: ...
@overload
def _build_mirascope_call(
    generation_public: GenerationPublic, fn: Callable[_P, _R]
) -> Callable[_P, Message | Stream]: ...
def _build_mirascope_call(
    generation_public: GenerationPublic,
    fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]],
) -> (
    Callable[_P, Message | Stream] | Callable[_P, Coroutine[Any, Any, Message | Stream]]
):
    """Build a Mirascope call object."""
    mirascope_prompt = prompt_template(generation_public.prompt_template)(fn)  # pyright: ignore [reportCallIssue, reportArgumentType]

    call_params = generation_public.call_params
    if generation_public.tools:
        pass
        # TODO: tools are not yet supported in managed mode
        # Skip tools in managed mode to avoid unexpected behavior
    elif response_model := generation_public.response_model:
        call_params["response_model"] = _create_model_from_json_schema(
            response_model.schema_data, response_model.name
        )
    mirascope_call = llm.call(**call_params)(mirascope_prompt)

    @wraps(mirascope_call)
    def inner(
        *args: _P.args, **kwargs: _P.kwargs
    ) -> Message | Coroutine[Any, Any, Message | Stream] | Stream:
        result = mirascope_call(*args, **kwargs)
        if fn_is_async(mirascope_call):

            async def async_wrapper() -> Message | Stream:
                final = await result
                if isinstance(final, CallResponse):
                    return Message(final)  # pyright: ignore [reportAbstractUsage]
                return Stream(stream=final)

            return async_wrapper()
        else:

            def sync_wrapper() -> Message | Stream:
                final = result
                if isinstance(final, CallResponse):
                    return Message(final)  # pyright: ignore [reportAbstractUsage]

                return Stream(stream=final)

            return sync_wrapper()

    return inner  # pyright: ignore [reportReturnType]


_ArgTypes: typing.TypeAlias = dict[str, str]


@overload
def generation(  # pyright: ignore [reportOverlappingOverload]
    custom_id: str | None = ..., managed: Literal[True] = ...
) -> ManagedGenerationVersioningDecorator: ...


@overload
def generation(
    custom_id: str | None = None, managed: Literal[False] = ...
) -> GenerationVersioningDecorator: ...


def generation(
    custom_id: str | None = None, managed: bool = False
) -> GenerationVersioningDecorator | ManagedGenerationVersioningDecorator:
    """The `generation` decorator for versioning and tracing LLM generations.\

    The decorated function will be versioned according to it's runnable lexical closure,
    and any call to the function will be traced and logged automatically.

    Returns:
        GenerationDecorator: The `generation` decorator return protocol.
    """

    @overload
    def decorator(
        fn: Callable[_P, Coroutine[Any, Any, _R]],
    ) -> Callable[_P, Coroutine[Any, Any, _R]]: ...

    @overload
    def decorator(fn: Callable[_P, _R]) -> Callable[_P, _R]: ...

    def decorator(
        fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]],
    ) -> Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]:
        is_mirascope_call = hasattr(fn, "__mirascope_call__") or managed
        prompt_template = (
            fn._prompt_template if hasattr(fn, "_prompt_template") else ""  # pyright: ignore[reportFunctionMemberAccess]
        )
        config = load_config()
        lilypad_client = LilypadClient(
            token=config.get("token", None),
        )
        if inspect.iscoroutinefunction(fn):

            def _create_inner_async(
                get_generation: Callable[[_ArgTypes], GenerationPublic],
            ) -> Callable[_P, Coroutine[Any, Any, _R]]:
                @call_safely(fn)
                async def _inner_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                    arg_types, arg_values = inspect_arguments(fn, *args, **kwargs)
                    generation = get_generation(arg_types)
                    token = current_generation.set(generation)
                    try:
                        # Check if this is the outermost generation (no previous generation)
                        is_outermost = token.old_value == Token.MISSING
                        with outermost_lock_context(is_outermost):
                            if not is_mirascope_call:
                                decorator_inner = _trace(
                                    generation=generation,
                                    arg_types=arg_types,
                                    arg_values=arg_values,
                                    prompt_template="",
                                )
                                return await decorator_inner(fn)(*args, **kwargs)
                            decorator_inner = create_mirascope_middleware(
                                generation,
                                arg_types,
                                arg_values,
                                True,
                                generation.prompt_template
                                if managed
                                else prompt_template,
                            )
                            return await decorator_inner(  # pyright: ignore [reportReturnType]
                                _build_mirascope_call(generation, fn) if managed else fn
                            )(*args, **kwargs)
                    finally:
                        current_generation.reset(token)

                return _inner_async

            def _get_active_version(arg_types: _ArgTypes) -> GenerationPublic:
                if not managed:
                    return lilypad_client.get_or_create_generation_version(
                        fn,
                        arg_types,
                        custom_id=custom_id,
                    )
                try:
                    return lilypad_client.get_generation_by_signature(
                        fn,
                    )
                except LilypadNotFoundError:
                    ui_link = f"{get_settings().remote_client_url}/projects/{lilypad_client.project_uuid}"
                    raise ValueError(
                        f"No generation found for function '{Closure.from_fn(fn).name}'. "
                        f"Please create a new generation at: {ui_link}"
                    )

            inner_async = _create_inner_async(_get_active_version)

            async def version_async(
                forced_version: int,
            ) -> Callable[_P, Coroutine[Any, Any, _R]]:
                specific_version_generation = lilypad_client.get_generation_by_version(
                    fn,
                    version=forced_version,
                )
                if not specific_version_generation:
                    raise ValueError(
                        f"Generation version {forced_version} not found for function: {fn.__name__}"
                    )

                def _get_specific_version(_: _ArgTypes) -> GenerationPublic:
                    return specific_version_generation

                return _create_inner_async(_get_specific_version)

            inner_async.version = version_async  # pyright: ignore [reportAttributeAccessIssue, reportFunctionMemberAccess]

            return inner_async

        else:

            def _create_inner_sync(
                get_generation: Callable[[_ArgTypes], GenerationPublic],
            ) -> Callable[_P, _R]:
                @call_safely(fn)
                def _inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                    arg_types, arg_values = inspect_arguments(fn, *args, **kwargs)
                    generation = get_generation(arg_types)
                    token = current_generation.set(generation)
                    try:
                        is_outermost = token.old_value == Token.MISSING
                        with outermost_lock_context(is_outermost):
                            if not is_mirascope_call:
                                decorator_inner = _trace(
                                    generation=generation,
                                    arg_types=arg_types,
                                    arg_values=arg_values,
                                    prompt_template="",
                                )
                                return decorator_inner(fn)(*args, **kwargs)  # pyright: ignore [reportReturnType]
                            decorator_inner = create_mirascope_middleware(
                                generation,
                                arg_types,
                                arg_values,
                                False,
                                generation.prompt_template
                                if managed
                                else prompt_template,
                            )
                            return decorator_inner(
                                _build_mirascope_call(generation, fn) if managed else fn
                            )(*args, **kwargs)  # pyright: ignore [reportReturnType]
                    finally:
                        current_generation.reset(token)

                return _inner  # pyright: ignore [reportReturnType]

            def _get_active_version(arg_types: _ArgTypes) -> GenerationPublic:
                if not managed:
                    return lilypad_client.get_or_create_generation_version(
                        fn, arg_types, custom_id=custom_id
                    )
                try:
                    return lilypad_client.get_generation_by_signature(fn)
                except LilypadNotFoundError:
                    ui_link = f"{get_settings().remote_client_url}/projects/{lilypad_client.project_uuid}"
                    raise ValueError(
                        f"No generation found for function '{Closure.from_fn(fn).name}'. "
                        f"Please create a new generation at: {ui_link}"
                    )

            inner = _create_inner_sync(_get_active_version)

            def version_sync(
                forced_version: int,
            ) -> Callable[_P, _R]:
                specific_version_generation = lilypad_client.get_generation_by_version(
                    fn,
                    version=forced_version,
                )
                if not specific_version_generation:
                    raise ValueError(
                        f"Generation version {forced_version} not found for function: {fn.__name__}"
                    )

                def _get_specific_version(_: _ArgTypes) -> GenerationPublic:
                    return specific_version_generation

                return _create_inner_sync(_get_specific_version)

            inner.version = version_sync  # pyright: ignore [reportAttributeAccessIssue, reportFunctionMemberAccess]

            return inner

    return decorator  # pyright: ignore [reportReturnType]
