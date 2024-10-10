"""The lilypad `llm_fn` decorator."""

import inspect
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import (
    Any,
    ParamSpec,
    Protocol,
    TypeVar,
    cast,
    overload,
)

from lilypad._trace import trace
from lilypad.server import client

from ._utils import (
    get_llm_function_version,
    inspect_arguments,
    traced_synced_llm_function_constructor,
)

_P = ParamSpec("_P")
_R = TypeVar("_R")

lilypad_client = client.LilypadClient(base_url="http://localhost:8000/api", timeout=10)


class LLMFn(Protocol):
    """Protocol for the `llm_fn` decorator return type."""

    @overload
    def __call__(
        self, fn: Callable[_P, Coroutine[Any, Any, _R]]
    ) -> Callable[_P, Coroutine[Any, Any, _R]]: ...

    @overload
    def __call__(self, fn: Callable[_P, _R]) -> Callable[_P, _R]: ...

    def __call__(
        self, fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]
    ) -> Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]:
        """Protocol `call` definition for `llm_fn` decorator return type."""
        ...


def llm_fn(synced: bool = False) -> LLMFn:
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
                arg_types, arg_values = inspect_arguments(fn, *args, **kwargs)
                version = get_llm_function_version(fn, arg_types, synced)
                trace_decorator = trace(
                    llm_function_id=version.llm_fn.id,
                    arg_types=arg_types,
                    arg_values=arg_values,
                    lexical_closure=version.llm_fn.code,
                    prompt_template=version.fn_params.prompt_template
                    if version.fn_params
                    else "",
                    version=version.version,
                )

                if not synced:
                    return cast(_R, await trace_decorator(fn)(*args, **kwargs))

                if not version.fn_params:
                    raise ValueError(f"Synced function {fn.__name__} has no params.")

                return await traced_synced_llm_function_constructor(
                    version.fn_params, trace_decorator
                )(fn)(*args, **kwargs)

            return inner_async

        else:

            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                arg_types, arg_values = inspect_arguments(fn, *args, **kwargs)
                version = get_llm_function_version(fn, arg_types, synced)
                trace_decorator = trace(
                    llm_function_id=version.llm_fn.id,
                    arg_types=arg_types,
                    arg_values=arg_values,
                    lexical_closure=version.llm_fn.code,
                    prompt_template=version.fn_params.prompt_template
                    if version.fn_params
                    else "",
                    version=version.version,
                )

                if not synced:
                    return cast(_R, trace_decorator(fn)(*args, **kwargs))

                if not version.fn_params:
                    raise ValueError(f"Synced function {fn.__name__} has no params.")

                return traced_synced_llm_function_constructor(
                    version.fn_params, trace_decorator
                )(fn)(*args, **kwargs)  # pyright: ignore [reportReturnType]

            return inner

    return decorator
