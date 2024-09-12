"""Utilities for the `lilypad` library."""

import inspect
from collections.abc import Callable, Coroutine
from typing import Any, ParamSpec, TypeVar

from typing_extensions import TypeIs

_P = ParamSpec("_P")
_R = TypeVar("_R")


def fn_is_async(
    fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]],
) -> TypeIs[Callable[_P, Coroutine[Any, Any, _R]]]:
    """Type check for if `fn` is asynchronous."""
    return inspect.iscoroutinefunction(fn)
