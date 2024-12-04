"""The `traces` module for automatically versioning and tracing LLM functions."""

import inspect
import json
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, ParamSpec, Protocol, TypeVar, overload
from uuid import UUID

from opentelemetry.trace import get_tracer
from opentelemetry.util.types import AttributeValue
from pydantic import BaseModel

from ._utils import create_mirascope_middleware, inspect_arguments, load_config
from .server.client import LilypadClient
from .server.settings import get_settings

_P = ParamSpec("_P")
_R = TypeVar("_R")

config = load_config()
settings = get_settings()
lilypad_client = LilypadClient(
    timeout=10,
    token=config.get("token", None),
)


class TraceDecorator(Protocol):
    """Protocol for the `trace` decorator return type."""

    @overload
    def __call__(
        self, fn: Callable[_P, Coroutine[Any, Any, _R]]
    ) -> Callable[_P, Coroutine[Any, Any, _R]]: ...

    @overload
    def __call__(self, fn: Callable[_P, _R]) -> Callable[_P, _R]: ...

    def __call__(
        self, fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]
    ) -> Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]:
        """Protocol `call` definition for `trace` decorator return type."""
        ...


def _trace(
    version_uuid: UUID,
    arg_types: dict[str, str],
    arg_values: dict[str, Any],
    lexical_closure: str,
    prompt_template: str = "",
    version_num: int | None = None,
) -> TraceDecorator:
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
                    results = str(output)
                    if isinstance(output, BaseModel):
                        results = str(output.model_dump())
                    attributes: dict[str, AttributeValue] = {
                        "lilypad.project_uuid": str(lilypad_client.project_uuid)
                        if lilypad_client.project_uuid
                        else 0,
                        "lilypad.function_name": fn.__name__,
                        "lilypad.version_num": version_num if version_num else -1,
                        "lilypad.version_uuid": str(version_uuid),
                        "lilypad.arg_types": json.dumps(arg_types),
                        "lilypad.arg_values": json.dumps(arg_values),
                        "lilypad.lexical_closure": lexical_closure,
                        "lilypad.prompt_template": prompt_template,
                        "lilypad.output": results,
                        "lilypad.is_async": True,
                    }
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
                    results = str(output)
                    if isinstance(output, BaseModel):
                        results = str(output.model_dump())
                    attributes: dict[str, AttributeValue] = {
                        "lilypad.project_uuid": str(lilypad_client.project_uuid)
                        if lilypad_client.project_uuid
                        else 0,
                        "lilypad.function_name": fn.__name__,
                        "lilypad.version_num": version_num if version_num else -1,
                        "lilypad.version_uuid": str(version_uuid),
                        "lilypad.arg_types": json.dumps(arg_types),
                        "lilypad.arg_values": json.dumps(arg_values),
                        "lilypad.lexical_closure": lexical_closure,
                        "lilypad.prompt_template": prompt_template,
                        "lilypad.output": results,
                        "lilypad.is_async": False,
                    }
                    span.set_attributes(attributes)
                return output  # pyright: ignore [reportReturnType]

            return inner

    return decorator


def trace() -> TraceDecorator:
    """The `trace` decorator for automatically versioning and tracing LLM functions.

    The decorated function will be versioned according to it's lexical closure, and any
    calls to the function will be traced and logged automatically.

    Returns:
        TraceDecorator: The `trace` decorator.
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
                version = lilypad_client.get_or_create_function_version(fn, arg_types)
                if not is_mirascope_call:
                    decorator = _trace(
                        version_uuid=version.uuid,
                        arg_types=arg_types,
                        arg_values=arg_values,
                        lexical_closure=version.function.code,
                        prompt_template="",
                        version_num=version.version_num,
                    )
                    return await decorator(fn)(*args, **kwargs)
                decorator = create_mirascope_middleware(
                    version, arg_types, arg_values, True, prompt_template
                )
                return await decorator(fn)(*args, **kwargs)

            return inner_async

        else:

            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                arg_types, arg_values = inspect_arguments(fn, *args, **kwargs)
                version = lilypad_client.get_or_create_function_version(fn, arg_types)
                if not is_mirascope_call:
                    decorator = _trace(
                        version_uuid=version.uuid,
                        arg_types=arg_types,
                        arg_values=arg_values,
                        lexical_closure=version.function.code,
                        prompt_template="",
                        version_num=version.version_num,
                    )
                    return decorator(fn)(*args, **kwargs)  # pyright: ignore [reportReturnType]
                decorator = create_mirascope_middleware(
                    version, arg_types, arg_values, False, prompt_template
                )
                return decorator(fn)(*args, **kwargs)  # pyright: ignore [reportReturnType]

            return inner

    return decorator


__all__ = ["trace"]
