"""The `trace` decorator, which is used to instrument functions for LLM API calls."""

import inspect
import json
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import (
    Any,
    ParamSpec,
    Protocol,
    TypeVar,
    overload,
)

from opentelemetry.trace import get_tracer
from opentelemetry.util.types import AttributeValue

_P = ParamSpec("_P")
_R = TypeVar("_R")


class Trace(Protocol):
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
        """Protocol `call` definition for `prompt` decorator return type."""
        ...


def trace(
    llm_function_id: int,
    arg_types: dict[str, str],
    arg_values: dict[str, Any],
    lexical_closure: str,
    prompt_template: str = "",
    version: int | None = None,
) -> Trace:
    """Returns a decorator for turining a typed function into an LLM API call."""

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
                    span.set_attributes(
                        {
                            "lilypad.function_name": fn.__name__,
                            "lilypad.version": version if version else "",
                            "lilypad.llm_function_id": llm_function_id,
                            "lilypad.arg_types": json.dumps(arg_types),
                            "lilypad.arg_values": json.dumps(arg_values),
                            "lilypad.lexical_closure": lexical_closure,
                            "lilypad.prompt_template": prompt_template,
                            "lilypad.output": str(output),
                            "lilypad.is_async": True,
                        }
                    )
                return output

            return inner_async

        else:

            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                with get_tracer("lilypad").start_as_current_span(
                    f"{fn.__name__}"
                ) as span:
                    output = fn(*args, **kwargs)
                    attributes: dict[str, AttributeValue] = {
                        "lilypad.function_name": fn.__name__,
                        "lilypad.version": version if version else "",
                        "lilypad.llm_function_id": llm_function_id,
                        "lilypad.arg_types": json.dumps(arg_types),
                        "lilypad.arg_values": json.dumps(arg_values),
                        "lilypad.lexical_closure": lexical_closure,
                        "lilypad.prompt_template": prompt_template,
                        "lilypad.output": str(output),
                        "lilypad.is_async": False,
                    }
                    span.set_attributes(attributes)
                return output  # pyright: ignore [reportReturnType]

            return inner

    return decorator
