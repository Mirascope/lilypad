"""Tracing decorator implementation for Lilypad SDK."""

from __future__ import annotations

import functools
import inspect
from dataclasses import dataclass
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    ParamSpec,
    TypeVar,
    cast,
    overload,
    Protocol,
)

from .spans import Span

P = ParamSpec("P")
R = TypeVar("R")


def _get_qualname(fn: Callable) -> str:
    """Get simplified qualified name for a function.

    Args:
        fn: The function to get the name from.

    Returns:
        Simplified qualified name without <locals> prefix.
    """
    qualname = getattr(
        fn, "__qualname__", fn.__name__ if hasattr(fn, "__name__") else "unknown"
    )
    if "<locals>." in qualname:
        parts = qualname.split("<locals>.")
        return parts[-1]
    return qualname


def _is_async(fn: Callable) -> bool:
    """Check if a function is async.

    Args:
        fn: The function to check.

    Returns:
        True if the function is async, False otherwise.
    """
    return inspect.iscoroutinefunction(fn)


@dataclass
class _TraceConfig:
    """Configuration for trace decorator."""

    tags: tuple[str, ...] = ()


class TraceResult(Generic[R]):
    """Per-call handle returned by .wrap() methods.

    Provides access to the response and per-call operations for annotation,
    tagging, and assignment within a specific trace span context.
    """

    def __init__(
        self, response: R, span_id: str | None = None, trace_id: str | None = None
    ) -> None:
        """Initialize a trace result with the wrapped response.

        Args:
            response: The actual function response.
            span_id: Optional span ID from the trace.
            trace_id: Optional trace ID from the trace.
        """
        self.response = response
        self._span_id = span_id
        self._trace_id = trace_id
        self._function_uuid: str | None = None

    def annotate(
        self,
        *,
        label: str | None = None,
        data: dict[str, Any] | None = None,
        reasoning: str | None = None,
    ) -> None:
        """Annotate the current trace span with additional metadata.

        Args:
            label: Optional label for the annotation.
            data: Optional structured data to attach.
            reasoning: Optional reasoning text explaining the annotation.
        """
        raise NotImplementedError("TraceResult.annotate not yet implemented")

    def tag(self, *tags: str) -> None:
        """Add tags to the current trace span.

        Args:
            *tags: Variable number of string tags to add.
        """
        raise NotImplementedError("TraceResult.tag not yet implemented")

    def assign(self, *emails: str) -> None:
        """Assign the trace to specific users by email.

        Args:
            *emails: Variable number of email addresses to assign.
        """
        raise NotImplementedError("TraceResult.assign not yet implemented")

    @property
    def span_id(self) -> str | None:
        """Get the current span ID if available.

        Returns:
            The span ID or None if not available.
        """
        return self._span_id

    @property
    def trace_id(self) -> str | None:
        """Get the current trace ID if available.

        Returns:
            The trace ID or None if not available.
        """
        return self._trace_id

    @property
    def function_uuid(self) -> str | None:
        """Get the function UUID if available.

        Returns:
            The function UUID or None if not available.
        """
        return self._function_uuid


class Traced(Protocol[P, R]):
    """Protocol for callable objects with tracing capability.

    Provides the base interface for traced functions that can be called
    normally or with wrapped results for detailed span control.
    """

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Execute the traced function normally, returning the original result."""
        ...

    @overload
    def wrap(self: Traced[P, R], *args: P.args, **kwargs: P.kwargs) -> TraceResult[R]:
        """Wrap synchronous function execution with trace result."""
        ...

    @overload
    def wrap(
        self: Traced[P, Awaitable[R]], *args: P.args, **kwargs: P.kwargs
    ) -> Awaitable[TraceResult[R]]:
        """Wrap asynchronous function execution with trace result."""
        ...

    def annotate(
        self,
        *,
        label: str | None = ...,
        data: dict[str, Any] | None = ...,
        reasoning: str | None = ...,
    ) -> None:
        """Global annotation helper (no-op by default, prefer per-call via wrap)."""
        ...

    def tag(self, *tags: str) -> None:
        """Global tagging helper (no-op by default, prefer per-call via wrap)."""
        ...

    def assign(self, *emails: str) -> None:
        """Global assignment helper (no-op by default, prefer per-call via wrap)."""
        ...


class _TraceWrapper(Generic[P, R]):
    """Callable wrapper returned by @trace decorator."""

    def __init__(self, fn: Callable[P, R], cfg: _TraceConfig) -> None:
        """Initialize the trace wrapper.

        Args:
            fn: The function to wrap.
            cfg: Trace configuration.
        """
        self._fn = fn
        self._cfg = cfg
        self._is_async = _is_async(fn)
        self._span_name = _get_qualname(fn)

        functools.update_wrapper(self, fn)

    def _execute_sync(
        self, *args: P.args, **kwargs: P.kwargs
    ) -> tuple[R, str | None, str | None]:
        """Execute synchronous function with span context.

        Returns:
            Tuple of (result, span_id, trace_id).
        """
        with Span(self._span_name) as s:
            attributes = {
                "lilypad.type": "trace",
                "lilypad.fn.qualname": _get_qualname(self._fn),
                "lilypad.fn.module": getattr(self._fn, "__module__", ""),
                "lilypad.fn.is_async": self._is_async,
            }
            if self._cfg.tags:
                attributes["lilypad.trace.tags"] = self._cfg.tags

            s.set(**attributes)
            result = self._fn(*args, **kwargs)

            span_id = s.span_id
            trace_id = None
            # Get trace_id from OTel span context if available
            span_obj = getattr(s, "_span", None)
            if span_obj and hasattr(span_obj, "get_span_context"):
                context = span_obj.get_span_context()
                if context and hasattr(context, "trace_id"):
                    trace_id = format(context.trace_id, "032x")

            return result, span_id, trace_id

    async def _execute_async(
        self, *args: P.args, **kwargs: P.kwargs
    ) -> tuple[Any, str | None, str | None]:
        """Execute asynchronous function with span context.

        Returns:
            Tuple of (result, span_id, trace_id).
        """
        with Span(self._span_name) as s:
            attributes = {
                "lilypad.type": "trace",
                "lilypad.fn.qualname": _get_qualname(self._fn),
                "lilypad.fn.module": getattr(self._fn, "__module__", ""),
                "lilypad.fn.is_async": self._is_async,
            }
            if self._cfg.tags:
                attributes["lilypad.trace.tags"] = self._cfg.tags

            s.set(**attributes)
            result = await cast(Awaitable[Any], self._fn(*args, **kwargs))

            span_id = s.span_id
            trace_id = None
            # Get trace_id from OTel span context if available
            span_obj = getattr(s, "_span", None)
            if span_obj and hasattr(span_obj, "get_span_context"):
                context = span_obj.get_span_context()
                if context and hasattr(context, "trace_id"):
                    trace_id = format(context.trace_id, "032x")

            return result, span_id, trace_id

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Execute the traced function normally.

        Args:
            *args: Positional arguments for the wrapped function.
            **kwargs: Keyword arguments for the wrapped function.

        Returns:
            The original function's return value.
        """
        if self._is_async:

            async def async_wrapper() -> R:
                result, _, _ = await self._execute_async(*args, **kwargs)
                return result

            return cast(R, async_wrapper())
        else:
            result, _, _ = self._execute_sync(*args, **kwargs)
            return result

    def wrap(self, *args: P.args, **kwargs: P.kwargs) -> Any:
        """Execute with trace wrapping.

        Args:
            *args: Positional arguments for the wrapped function.
            **kwargs: Keyword arguments for the wrapped function.

        Returns:
            TraceResult containing the response and trace operations for sync functions,
            or Awaitable[TraceResult] for async functions.
        """
        if self._is_async:

            async def async_wrapper() -> TraceResult:
                result, span_id, trace_id = await self._execute_async(*args, **kwargs)
                return TraceResult(result, span_id=span_id, trace_id=trace_id)

            return async_wrapper()
        else:
            result, span_id, trace_id = self._execute_sync(*args, **kwargs)
            return TraceResult(result, span_id=span_id, trace_id=trace_id)

    def annotate(
        self,
        *,
        label: str | None = None,
        data: dict[str, Any] | None = None,
        reasoning: str | None = None,
    ) -> None:
        """Global annotation helper.

        Args:
            label: Optional label for the annotation.
            data: Optional structured data to attach.
            reasoning: Optional reasoning text explaining the annotation.
        """
        raise NotImplementedError("_TraceWrapper.annotate not yet implemented")

    def tag(self, *tags: str) -> None:
        """Global tagging helper.

        Args:
            *tags: Variable number of string tags to add.
        """
        raise NotImplementedError("_TraceWrapper.tag not yet implemented")

    def assign(self, *emails: str) -> None:
        """Global assignment helper.

        Args:
            *emails: Variable number of email addresses to assign.
        """
        raise NotImplementedError("_TraceWrapper.assign not yet implemented")


@overload
def trace(fn: Callable[P, R], /, *, tags: list[str] | None = None) -> Traced[P, R]:
    """Decorate a synchronous function with tracing capability.

    Args:
        fn: The function to trace.
        tags: Optional list of tags to apply to all spans.

    Returns:
        A traced callable with wrap() and annotation methods.
    """
    ...


@overload
def trace(
    fn: Callable[P, Awaitable[R]], /, *, tags: list[str] | None = None
) -> Traced[P, Awaitable[R]]:
    """Decorate an asynchronous function with tracing capability.

    Args:
        fn: The async function to trace.
        tags: Optional list of tags to apply to all spans.

    Returns:
        A traced async callable with wrap() and annotation methods.
    """
    ...


@overload
def trace(*, tags: list[str] | None = None) -> Callable[[Callable[P, R]], Traced[P, R]]:
    """Create a trace decorator for synchronous functions.

    Args:
        tags: Optional list of tags to apply to all spans.

    Returns:
        A decorator that adds tracing capability to functions.
    """
    ...


@overload
def trace(
    *, tags: list[str] | None = None
) -> Callable[[Callable[P, Awaitable[R]]], Traced[P, Awaitable[R]]]:
    """Create a trace decorator for asynchronous functions.

    Args:
        tags: Optional list of tags to apply to all spans.

    Returns:
        A decorator that adds tracing capability to async functions.
    """
    ...


def trace(
    fn: Callable[P, R] | None = None, /, *, tags: list[str] | None = None
) -> Callable[P, R] | Callable[[Callable[P, R]], _TraceWrapper[P, R]]:
    """Add tracing capability to a callable function.

    Can be used as a decorator with or without arguments. Preserves the original
    function's return type by default, with opt-in wrapping via the wrap() method.

    Args:
        fn: The function to trace (when used without parentheses).
        tags: Optional list of tags to apply to all spans.

    Returns:
        A traced callable or a decorator function.

    Examples:
        >>> @trace
        ... def my_func(x: int) -> int:
        ...     return x * 2

        >>> @trace(tags=["production", "api"])
        ... async def async_func() -> str:
        ...     return "result"
    """

    def _decorator(func: Callable[P, R]) -> _TraceWrapper[P, R]:
        """Inner decorator that creates the trace wrapper.

        Args:
            func: The function to wrap.

        Returns:
            A traced wrapper around the function.
        """
        normalized_tags = tuple(sorted(set(tags or [])))
        config = _TraceConfig(tags=normalized_tags)
        return cast(Any, _TraceWrapper(func, config))

    if fn is None:
        return _decorator
    else:
        return _decorator(fn)
