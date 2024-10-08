"""The `trace` decorator, which is used to instrument functions for LLM API calls."""

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

from .utils import fn_is_async

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
    version_hash: str,
    input_values: dict[str, Any],
    input_types: dict[str, type[Any]],
    lexical_closure: str,
    prompt_template: str = "",
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
        if fn_is_async(fn):

            @wraps(fn)
            async def inner_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                with get_tracer("lilypad").start_as_current_span(
                    f"{fn.__name__}"
                ) as span:
                    output = fn(*args, **kwargs)
                    span.set_attributes(
                        {
                            "lilypad.function_name": fn.__name__,
                            "lilypad.version_hash": version_hash,
                            "lilypad.llm_function_id": llm_function_id,
                            "lilypad.input_values": json.dumps(input_values),
                            "lilypad.input_types": json.dumps(input_types),
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
                        "lilypad.version_hash": version_hash,
                        "lilypad.llm_function_id": llm_function_id,
                        "lilypad.input_values": json.dumps(input_values),
                        "lilypad.input_types": json.dumps(input_types),
                        "lilypad.lexical_closure": lexical_closure,
                        "lilypad.prompt_template": prompt_template,
                        "lilypad.output": str(output),
                        "lilypad.is_async": False,
                    }
                    span.set_attributes(attributes)
                return output

            return inner

    return decorator
