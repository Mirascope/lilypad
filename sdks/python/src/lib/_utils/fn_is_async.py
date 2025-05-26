import inspect
from typing import Any, TypeVar
from collections.abc import Callable, Awaitable, Coroutine
from typing_extensions import TypeIs

_R = TypeVar("_R")


def fn_is_async(
    fn: Callable[..., Awaitable[_R] | Coroutine[Any, Any, _R]] | Callable[..., _R],
) -> TypeIs[Callable[..., Coroutine[Any, Any, _R]]]:
    if inspect.iscoroutinefunction(fn):
        return True

    # Check if it's a wrapper around an `async def` function (using functools.wraps).
    _fn = fn
    while hasattr(_fn, "__wrapped__"):
        _fn = _fn.__wrapped__
        if inspect.iscoroutinefunction(_fn):
            return True
    return False


__all__ = ["fn_is_async"]
