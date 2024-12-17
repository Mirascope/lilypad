"""The `generations` module for automatically versioning and tracing LLM generations."""

import inspect
import json
from collections.abc import Callable, Coroutine
from contextvars import ContextVar
from functools import wraps
from typing import Any, ParamSpec, Protocol, TypeVar, overload

from opentelemetry.trace import get_tracer
from opentelemetry.util.types import AttributeValue
from pydantic import BaseModel

from ._utils import create_mirascope_middleware, inspect_arguments, load_config
from .server.client import LilypadClient
from .server.models import GenerationPublic
from .server.settings import get_settings

_P = ParamSpec("_P")
_R = TypeVar("_R")

config = load_config()
settings = get_settings()
lilypad_client = LilypadClient(
    timeout=10,
    token=config.get("token", None),
)


current_generation: ContextVar[GenerationPublic | None] = ContextVar(
    "current_generation", default=None
)


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


def _construct_trace_attributes(
    generation: GenerationPublic,
    arg_types: dict[str, str],
    arg_values: dict[str, Any],
    prompt_template: str,
    output: Any,
    is_async: bool,
) -> dict[str, AttributeValue]:
    if isinstance(output, BaseModel):
        output = str(output.model_dump())
    return {
        "lilypad.project_uuid": str(lilypad_client.project_uuid)
        if lilypad_client.project_uuid
        else 0,
        "lilypad.type": "generation",
        "lilypad.generation.uuid": str(generation.uuid),
        "lilypad.generation.name": generation.name,
        "lilypad.generation.signature": generation.signature,
        "lilypad.generation.code": generation.code,
        "lilypad.generation.arg_types": json.dumps(arg_types),
        "lilypad.generation.arg_values": json.dumps(arg_values),
        "lilypad.generation.prompt_template": prompt_template,
        "lilypad.generation.output": str(output),
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
                with get_tracer("lilypad").start_as_current_span(
                    f"{fn.__name__}"
                ) as span:
                    output = await fn(*args, **kwargs)
                    attributes: dict[str, AttributeValue] = _construct_trace_attributes(
                        generation, arg_types, arg_values, prompt_template, output, True
                    )
                    span.set_attributes(attributes)
                return output  # pyright: ignore [reportReturnType]

            return inner_async

        else:

            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                with get_tracer("lilypad").start_as_current_span(
                    f"{fn.__name__}"
                ) as span:
                    output = fn(*args, **kwargs)
                    attributes: dict[str, AttributeValue] = _construct_trace_attributes(
                        generation,
                        arg_types,
                        arg_values,
                        prompt_template,
                        output,
                        False,
                    )
                    span.set_attributes(attributes)
                return output  # pyright: ignore [reportReturnType]

            return inner

    return decorator


def generation() -> GenerationDecorator:
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
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def inner_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                arg_types, arg_values = inspect_arguments(fn, *args, **kwargs)
                generation = lilypad_client.get_or_create_generation_version(
                    fn, arg_types
                )
                token = current_generation.set(generation)
                try:
                    if not is_mirascope_call:
                        decorator = _trace(
                            generation=generation,
                            arg_types=arg_types,
                            arg_values=arg_values,
                            prompt_template="",
                        )
                        return await decorator(fn)(*args, **kwargs)
                    decorator = create_mirascope_middleware(
                        generation, arg_types, arg_values, True, prompt_template
                    )
                    return await decorator(fn)(*args, **kwargs)
                finally:
                    current_generation.reset(token)

            return inner_async

        else:

            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                arg_types, arg_values = inspect_arguments(fn, *args, **kwargs)
                generation = lilypad_client.get_or_create_generation_version(
                    fn, arg_types
                )
                token = current_generation.set(generation)
                try:
                    if not is_mirascope_call:
                        decorator = _trace(
                            generation=generation,
                            arg_types=arg_types,
                            arg_values=arg_values,
                            prompt_template="",
                        )
                        return decorator(fn)(*args, **kwargs)  # pyright: ignore [reportReturnType]
                    decorator = create_mirascope_middleware(
                        generation, arg_types, arg_values, False, prompt_template
                    )
                    return decorator(fn)(*args, **kwargs)  # pyright: ignore [reportReturnType]
                finally:
                    current_generation.reset(token)

            return inner

    return decorator
