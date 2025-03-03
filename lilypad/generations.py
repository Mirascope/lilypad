"""The `generations` module for automatically versioning and tracing LLM generations."""

import json
from collections.abc import Callable, Coroutine, Generator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any, ParamSpec, TypeAlias, TypeVar, overload

from fastapi.encoders import jsonable_encoder
from opentelemetry.util.types import AttributeValue

from ._utils import (
    ArgTypes,
    ArgValues,
    call_safely,
    create_mirascope_middleware,
    fn_is_async,
    inspect_arguments,
    load_config,
)
from .server.client import LilypadClient
from .server.schemas import GenerationPublic
from .traces import TraceDecorator, _get_batch_span_processor, _trace

_P = ParamSpec("_P")
_R = TypeVar("_R")

GenerationDecorator: TypeAlias = TraceDecorator

current_generation: ContextVar[GenerationPublic | None] = ContextVar(
    "current_generation", default=None
)


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
    lilypad_client: LilypadClient,
    custom_id: str | None,
    fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]],
    *args: Any,
    **kwargs: Any,
) -> Generator[tuple[ArgTypes, ArgValues, GenerationPublic], None, None]:
    arg_types, arg_values = inspect_arguments(fn, *args, **kwargs)
    generation_ = lilypad_client.get_or_create_generation_version(
        fn, arg_types, custom_id=custom_id
    )
    token = current_generation.set(generation_)
    try:
        # Check if this is the outermost generation (no previous generation)
        is_outermost = token.old_value == Token.MISSING
        with _outermost_lock_context(is_outermost):
            yield arg_types, arg_values, generation_
    finally:
        current_generation.reset(token)


def generation(custom_id: str | None = None) -> GenerationDecorator:
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
        is_mirascope_call = hasattr(fn, "__mirascope_call__")
        prompt_template = (
            fn._prompt_template if hasattr(fn, "_prompt_template") else ""  # pyright: ignore[reportFunctionMemberAccess]
        )
        config = load_config()
        lilypad_client = LilypadClient(
            token=config.get("token", None),
        )
        if fn_is_async(fn):

            @call_safely(fn)
            async def inner_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                with _generation_context(
                    lilypad_client, custom_id, fn, *args, **kwargs
                ) as (arg_types, arg_values, generation_):
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
                        return await decorator_inner(fn)(*args, **kwargs)
                    decorator_inner = create_mirascope_middleware(
                        generation_, arg_types, arg_values, True, prompt_template
                    )
                    return await decorator_inner(fn)(*args, **kwargs)

            return inner_async

        else:

            @call_safely(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                with _generation_context(
                    lilypad_client, custom_id, fn, *args, **kwargs
                ) as (arg_types, arg_values, generation_):
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
                        return decorator_inner(fn)(*args, **kwargs)  # pyright: ignore [reportReturnType]
                    decorator_inner = create_mirascope_middleware(
                        generation_, arg_types, arg_values, False, prompt_template
                    )
                    return decorator_inner(fn)(*args, **kwargs)  # pyright: ignore [reportReturnType]

            return inner  # pyright: ignore [reportReturnType]

    return decorator
