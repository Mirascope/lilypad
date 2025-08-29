"""Remote execution decorator implementation for Lilypad SDK."""

from __future__ import annotations

from typing import Awaitable, Callable, Generic, ParamSpec, TypeVar, overload

from ..types import RemoteCap

P = ParamSpec("P")
R = TypeVar("R")


class _RemoteWrapper(Generic[P, R]):
    """Callable wrapper returned by @remote decorator."""

    def __init__(self, fn: Callable[P, R]) -> None:
        """Initialize the remote wrapper.

        Args:
            fn: The function to wrap with remote capability.
        """
        self._fn = fn
        self.__name__ = getattr(fn, "__name__", "unknown")
        self.__qualname__ = getattr(fn, "__qualname__", "unknown")
        self.__module__ = getattr(fn, "__module__", "")
        self.__doc__ = fn.__doc__
        self.__annotations__ = getattr(fn, "__annotations__", {})
        self.__wrapped__ = fn

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Execute the function locally.

        Args:
            *args: Positional arguments for the wrapped function.
            **kwargs: Keyword arguments for the wrapped function.

        Returns:
            The original function's return value.
        """
        raise NotImplementedError("_RemoteWrapper.__call__ not yet implemented")

    def execute_remote(
        self, target: str, *args: P.args, **kwargs: P.kwargs
    ) -> Awaitable[R]:
        """Execute the function on a remote target.

        Args:
            target: Remote target identifier (e.g., "gpu-a", "worker-1").
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            An awaitable that resolves to the function result.
        """
        raise NotImplementedError("_RemoteWrapper.execute_remote not yet implemented")

    def execute_remote_wrap(
        self, target: str, *args: P.args, **kwargs: P.kwargs
    ) -> Awaitable[object]:
        """Execute remotely with trace wrapping.

        Args:
            target: Remote target identifier (e.g., "gpu-a", "worker-1").
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            An awaitable that resolves to a TraceResult containing the response.
        """
        raise NotImplementedError(
            "_RemoteWrapper.execute_remote_wrap not yet implemented"
        )


@overload
def remote(fn: Callable[P, Awaitable[R]], /) -> RemoteCap[P, Awaitable[R]]:
    """Add remote execution capability to an asynchronous function.

    Args:
        fn: The async function to make remotely executable.

    Returns:
        A remote-capable async callable with execute_remote() methods.
    """
    ...


@overload
def remote(fn: Callable[P, R], /) -> RemoteCap[P, R]:
    """Add remote execution capability to a synchronous function.

    Args:
        fn: The function to make remotely executable.

    Returns:
        A remote-capable callable with execute_remote() methods.
    """
    ...


@overload
def remote() -> Callable[[Callable[P, R]], RemoteCap[P, R]]:
    """Create a remote decorator for synchronous functions.

    Returns:
        A decorator that adds remote execution capability to functions.
    """
    ...


def remote(
    fn: Callable[P, R] | None = None, /
) -> Callable[P, R] | Callable[[Callable[P, R]], _RemoteWrapper[P, R]]:
    """Add remote execution capability to a callable function.

    Enables functions to be executed on remote targets with automatic
    serialization and result handling. Always returns awaitable results
    for remote execution regardless of the original function type.

    Args:
        fn: The function to make remotely executable.

    Returns:
        A remote-capable callable or a decorator function.

    Examples:
        >>> @remote
        ... def compute(x: int) -> int:
        ...     return x * 2

        >>> @remote
        ... async def process(data: str) -> str:
        ...     return data.upper()
    """

    def _decorator(func: Callable[P, R]) -> _RemoteWrapper[P, R]:
        """Inner decorator that creates the remote wrapper.

        Args:
            func: The function to wrap.

        Returns:
            A remote-capable wrapper around the function.
        """
        return _RemoteWrapper(func)

    if fn is None:
        return _decorator
    else:
        return _decorator(fn)
