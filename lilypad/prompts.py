"""The lilypad `prompt` decorator."""

from collections.abc import Callable, Coroutine
from functools import wraps
from typing import (
    Any,
    ParamSpec,
    Protocol,
    TypeVar,
    overload,
)

from .utils import fn_is_async

_P = ParamSpec("_P")
_R = TypeVar("_R")


class Prompt(Protocol):
    """Protocol for the `prompt` decorator return type."""

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


def prompt() -> Prompt:
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
        # compute lexical closure of fn here
        # determine if there has been a version update

        if fn_is_async(fn):

            @wraps(fn)
            async def inner_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                # if version update, make update
                # trace call
                ...

            return inner_async

        else:

            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                # if version update, make update
                # trace call
                ...

            return inner

    return decorator
