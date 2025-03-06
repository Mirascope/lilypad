"""The `generations` module for automatically versioning and tracing LLM generations."""

import json
import typing
from collections.abc import Callable, Coroutine, Generator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from enum import Enum
from functools import wraps
from typing import (
    Any,
    Generic,
    Literal,
    ParamSpec,
    Protocol,
    TypeAlias,
    TypeVar,
    cast,
    overload,
)
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from mirascope import llm
from mirascope.core import prompt_template
from mirascope.core.base.types import Provider
from mirascope.llm.call_response import CallResponse
from opentelemetry.util.types import AttributeValue

from ._utils import (
    ArgTypes,
    ArgValues,
    Closure,
    call_safely,
    create_mirascope_middleware,
    fn_is_async,
    inspect_arguments,
    load_config,
)
from ._utils.middleware import SpanContextHolder
from .messages import Message
from .server.client import LilypadClient, LilypadNotFoundError
from .server.schemas import GenerationPublic
from .server.settings import get_settings
from .stream import Stream
from .traces import TraceDecorator, _get_batch_span_processor, _trace

_P = ParamSpec("_P")
_R = TypeVar("_R")
_R_CO = TypeVar("_R_CO", covariant=True)
T = TypeVar("T")


class GenerationMode(str, Enum):
    """Enum for generation return mode."""

    NO_WRAP = "no-wrap"
    WRAP = "wrap"


T_co = TypeVar("T_co", covariant=True)


class Generation(Generic[T]):
    """Container for a generation output, its metadata, and the associated trace/span ID."""

    def __init__(
        self,
        output: T,
        metadata: GenerationPublic,
        trace_id: int | None = None,
        span_id: int | None = None,
    ) -> None:
        """Initialize a Generation instance.

        Args:
            output: The generated output.
            metadata: The generation metadata.
            trace_id: Optional trace ID for this specific run.
            span_id: Optional span ID for this specific run
        """
        self.output = output
        self.metadata = metadata
        self.trace_id = trace_id
        self.span_id = span_id

        self.uuid: UUID = metadata.uuid
        self.name: str = metadata.name
        self.signature: str = metadata.signature
        self.version_num: int | None = metadata.version_num
        self.model: str | None = metadata.model
        self.provider: str | None = metadata.provider

    def __repr__(self) -> str:
        """String representation of Generation."""
        return (
            f"Generation(name='{self.name}', version={self.version_num}, "
            f"trace_id='{self.trace_id}', span_id='{self.span_id}' , output={self.output})"
        )


GenerationDecorator: TypeAlias = TraceDecorator

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


class SyncGenerationWrapFunction(Protocol[_P, _R]):
    """Protocol for the `generation` decorator return type with wrap mode."""

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> Generation[_R]:
        """Protocol for the `generation` decorator return type."""
        ...

    def version(self, forced_version: int) -> Callable[_P, Generation[_R]]:
        """Protocol for the `generation` decorator return type."""
        ...


class AsyncGenerationWrapFunction(Protocol[_P, _R]):
    """Protocol for the `generation` decorator return type with wrap mode."""

    def __call__(
        self, *args: _P.args, **kwargs: _P.kwargs
    ) -> Coroutine[Any, Any, Generation[_R]]:
        """Protocol for the `generation` decorator return type."""
        ...

    def version(
        self, forced_version: int
    ) -> Coroutine[Any, Any, Callable[_P, Coroutine[Any, Any, Generation[_R]]]]:
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


class GenerationVersioningWrapDecorator(Protocol):
    """Protocol for the `generation` decorator return type with wrap mode."""

    @overload
    def __call__(  # pyright: ignore [reportOverlappingOverload]
        self, fn: Callable[_P, Coroutine[Any, Any, _R]]
    ) -> AsyncGenerationWrapFunction[_P, _R]: ...

    @overload
    def __call__(self, fn: Callable[_P, _R]) -> SyncGenerationWrapFunction[_P, _R]: ...

    def __call__(
        self, fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]
    ) -> SyncGenerationWrapFunction[_P, _R] | AsyncGenerationWrapFunction[_P, _R]:
        """Protocol `call` definition for `generation` decorator return type."""
        ...


class ManagedGenerationVersioningWrapDecorator(Protocol):
    """Protocol for the `generation` decorator return type with wrap mode."""

    @overload
    def __call__(  # pyright: ignore [reportOverlappingOverload]
        self, fn: Callable[_P, Coroutine[Any, Any, _R]]
    ) -> AsyncGenerationWrapFunction[_P, Message | Stream]: ...

    @overload
    def __call__(
        self, fn: Callable[_P, _R]
    ) -> SyncGenerationWrapFunction[_P, Message | Stream]: ...

    def __call__(
        self, fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]
    ) -> (
        SyncGenerationWrapFunction[_P, Message | Stream]
        | AsyncGenerationWrapFunction[_P, Message | Stream]
    ):
        """Protocol `call` definition for `generation` decorator return type."""
        ...


@contextmanager
def _outermost_lock_context(enable_lock: bool) -> Generator[None, None, None]:
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


def _construct_trace_attributes(
    generation: GenerationPublic,
    arg_types: dict[str, str],
    arg_values: dict[str, Any],
    prompt_template: str,
) -> dict[str, AttributeValue]:
    jsonable_arg_values = {}
    for arg_name, arg_value in arg_values.items():
        try:
            serialized_arg_value = jsonable_encoder(arg_value)
        except ValueError:
            serialized_arg_value = "could not serialize"
        jsonable_arg_values[arg_name] = serialized_arg_value
    return {
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
    }


@contextmanager
def _generation_context(
    get_generation: Callable[[ArgTypes], GenerationPublic],
    fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]],
    *args: Any,
    **kwargs: Any,
) -> Generator[tuple[ArgTypes, ArgValues, GenerationPublic], None, None]:
    arg_types, arg_values = inspect_arguments(fn, *args, **kwargs)
    generation_ = get_generation(arg_types)
    token = current_generation.set(generation_)
    try:
        # Check if this is the outermost generation (no previous generation)
        is_outermost = token.old_value == Token.MISSING
        with _outermost_lock_context(is_outermost):
            yield arg_types, arg_values, generation_
    finally:
        current_generation.reset(token)


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

    if not generation_public.model:
        raise ValueError("Managed generation requires `model`")
    if not generation_public.provider:
        raise ValueError("Managed generation requires `provider`")
    mirascope_call = llm.call(
        provider=cast(Provider, generation_public.provider),
        model=generation_public.model,
        call_params=generation_public.call_params,
    )(mirascope_prompt)

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
    custom_id: str | None = None,
    managed: Literal[True] = True,
    mode: Literal[GenerationMode.WRAP] = GenerationMode.WRAP,
) -> ManagedGenerationVersioningWrapDecorator: ...


@overload
def generation(  # pyright: ignore [reportOverlappingOverload]
    custom_id: str | None = None,
    managed: Literal[False] = False,
    mode: Literal[GenerationMode.WRAP] = GenerationMode.WRAP,
) -> GenerationVersioningWrapDecorator: ...


@overload
def generation(  # pyright: ignore [reportOverlappingOverload]
    custom_id: str | None = None,
    managed: Literal[True] = True,
    mode: Literal[GenerationMode.NO_WRAP] = GenerationMode.NO_WRAP,
) -> ManagedGenerationVersioningDecorator: ...


@overload
def generation(
    custom_id: str | None = None,
    managed: Literal[False] = False,
    mode: Literal[GenerationMode.NO_WRAP] = GenerationMode.NO_WRAP,
) -> GenerationVersioningDecorator: ...


def generation(
    custom_id: str | None = None,
    managed: bool = False,
    mode: GenerationMode = GenerationMode.NO_WRAP,
) -> (
    GenerationVersioningDecorator
    | ManagedGenerationVersioningDecorator
    | GenerationVersioningWrapDecorator
    | ManagedGenerationVersioningWrapDecorator
):
    """The `generation` decorator for versioning and tracing LLM generations.

    The decorated function will be versioned according to it's runnable lexical closure,
    and any call to the function will be traced and logged automatically.

    Args:
        custom_id: Optional custom identifier for the generation
        managed: If True, uses managed mode that retrieves generation info from server
        mode: Controls whether to return the original output or wrap it in a Generation object

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
    ) -> (
        Callable[_P, _R]
        | Callable[_P, Coroutine[Any, Any, _R]]
        | Callable[_P, Generation[_R]]
        | Callable[_P, Coroutine[Any, Any, Generation[_R]]]
    ):
        is_mirascope_call = hasattr(fn, "__mirascope_call__") or managed
        prompt_template_value = (
            fn._prompt_template if hasattr(fn, "_prompt_template") else ""  # pyright: ignore[reportFunctionMemberAccess]
        )
        config = load_config()
        lilypad_client = LilypadClient(
            token=config.get("token", None),
        )
        if fn_is_async(fn):

            def _create_inner_async(
                get_generation: Callable[[_ArgTypes], GenerationPublic],
            ) -> (
                Callable[_P, Coroutine[Any, Any, _R]]
                | Callable[_P, Coroutine[Any, Any, Generation[_R]]]
            ):
                @call_safely(fn)  # pyright: ignore [reportArgumentType]
                async def _inner_async(
                    *args: _P.args, **kwargs: _P.kwargs
                ) -> _R | Generation[_R]:
                    with _generation_context(get_generation, fn, *args, **kwargs) as (
                        arg_types,
                        arg_values,
                        generation_,
                    ):
                        if not is_mirascope_call:
                            decorator_inner = _trace(
                                "generation",
                                _construct_trace_attributes(
                                    generation=generation_,
                                    arg_types=arg_types,
                                    arg_values=arg_values,
                                    prompt_template="",
                                ),
                            )
                            result = await decorator_inner(fn)(*args, **kwargs)
                            output, trace_id, span_id = (
                                result
                                if isinstance(result, tuple)
                                else (result, None, None)
                            )
                        else:
                            span_context_holder = SpanContextHolder()
                            decorator_inner = create_mirascope_middleware(
                                generation_,
                                arg_types,
                                arg_values,
                                True,
                                generation_.prompt_template
                                if managed
                                else prompt_template_value,
                                span_context_holder=span_context_holder,
                            )
                            output = await decorator_inner(  # pyright: ignore [reportReturnType]
                                _build_mirascope_call(generation_, fn)
                                if managed
                                else fn
                            )(*args, **kwargs)
                            if span_context := span_context_holder.span_context:
                                span_id = span_context.span_id
                                trace_id = span_context.trace_id
                            else:
                                trace_id = span_id = None
                        # Wrap output if in wrap mode
                        if mode == GenerationMode.WRAP:
                            return Generation(output, generation_, trace_id, span_id)  # pyright: ignore [reportReturnType]
                        return output  # pyright: ignore [reportReturnType]

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
            ) -> (
                Callable[_P, Coroutine[Any, Any, _R]]
                | Callable[_P, Coroutine[Any, Any, Generation[_R]]]
            ):
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
            ) -> Callable[_P, _R] | Callable[_P, Generation[_R]]:
                @call_safely(fn)  # pyright: ignore [reportArgumentType]
                def _inner(*args: _P.args, **kwargs: _P.kwargs) -> _R | Generation[_R]:
                    with _generation_context(get_generation, fn, *args, **kwargs) as (
                        arg_types,
                        arg_values,
                        generation_,
                    ):
                        if not is_mirascope_call:
                            decorator_inner = _trace(
                                "generation",
                                _construct_trace_attributes(
                                    generation=generation_,
                                    arg_types=arg_types,
                                    arg_values=arg_values,
                                    prompt_template="",
                                ),
                            )
                            result = decorator_inner(fn)(*args, **kwargs)
                            output, trace_id, span_id = (
                                result
                                if isinstance(result, tuple)
                                else (result, None, None)
                            )
                        else:
                            span_context_holder = SpanContextHolder()
                            decorator_inner = create_mirascope_middleware(
                                generation_,
                                arg_types,
                                arg_values,
                                False,
                                generation_.prompt_template
                                if managed
                                else prompt_template_value,
                                span_context_holder=span_context_holder,
                            )
                            output = decorator_inner(
                                _build_mirascope_call(generation_, fn)
                                if managed
                                else fn
                            )(*args, **kwargs)
                            if span_context := span_context_holder.span_context:
                                span_id = span_context.span_id
                                trace_id = span_context.trace_id
                            else:
                                trace_id = span_id = None
                        if mode == GenerationMode.WRAP:
                            return Generation(output, generation_, trace_id, span_id)  # pyright: ignore [reportReturnType]
                        return output  # pyright: ignore [reportReturnType]

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
            ) -> Callable[_P, _R] | Callable[_P, Generation[_R]]:
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
