"""A decorator for tracing functions."""

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar, overload

from openai import OpenAI

_P = ParamSpec("_P")
_R = TypeVar("_R")

client = OpenAI()


@overload
def trace(fn: Callable[_P, _R]) -> Callable[_P, _R]: ...


@overload
def trace(fn: None = None) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]: ...


def trace(
    fn: Callable[_P, _R] | None = None,
) -> Callable[_P, _R] | Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    """A decorator for tracing functions."""
    if fn is None:

        def decorator(fn: Callable[_P, _R]) -> Callable[_P, _R]:
            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                return fn(*args, **kwargs)

            return inner

        return decorator

    else:

        @wraps(fn)
        def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            return fn(*args, **kwargs)

        return inner
