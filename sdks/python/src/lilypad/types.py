"""Type definitions for Lilypad SDK tracing and capabilities."""

from __future__ import annotations

from typing import Any, Awaitable, Generic, ParamSpec, Protocol, TypeVar, overload

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")


class TraceResult(Generic[R]):
    """Per-call handle returned by .wrap()/..._wrap() methods.

    Provides access to the response and per-call operations for annotation,
    tagging, and assignment within a specific trace span context.
    """

    response: R

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
        ...

    def tag(self, *tags: str) -> None:
        """Add tags to the current trace span.

        Args:
            *tags: Variable number of string tags to add.
        """
        ...

    def assign(self, *emails: str) -> None:
        """Assign the trace to specific users by email.

        Args:
            *emails: Variable number of email addresses to assign.
        """
        ...

    @property
    def span_id(self) -> str | None:
        """Get the current span ID if available."""
        ...

    @property
    def trace_id(self) -> str | None:
        """Get the current trace ID if available."""
        ...

    @property
    def function_uuid(self) -> str | None:
        """Get the function UUID if available."""
        ...


class Traced(Protocol[P, R]):
    """Protocol for callable objects with tracing capability.

    Provides the base interface for traced functions that can be called
    normally or with wrapped results for detailed span control.
    """

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Execute the traced function normally, returning the original result."""
        ...

    @overload
    def wrap(self: Traced[P, T], *args: P.args, **kwargs: P.kwargs) -> TraceResult[T]:
        """Wrap synchronous function execution with trace result."""
        ...

    @overload
    def wrap(
        self: Traced[P, Awaitable[T]], *args: P.args, **kwargs: P.kwargs
    ) -> Awaitable[TraceResult[T]]:
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


class Versioned(Protocol[P, R], Traced[P, R]):
    """Protocol adding versioning capabilities to a traced callable.

    Extends Traced with version management, allowing execution of specific
    versions and version introspection.
    """

    @overload
    def run_version(
        self: Versioned[P, T], ref: VersionRef | str, *args: P.args, **kwargs: P.kwargs
    ) -> T:
        """Run a specific version of a synchronous function."""
        ...

    @overload
    def run_version(
        self: Versioned[P, Awaitable[T]],
        ref: VersionRef | str,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> Awaitable[T]:
        """Run a specific version of an asynchronous function."""
        ...

    @overload
    def run_version_wrap(
        self: Versioned[P, T], ref: VersionRef | str, *args: P.args, **kwargs: P.kwargs
    ) -> TraceResult[T]:
        """Run a specific version of a synchronous function with trace wrapping."""
        ...

    @overload
    def run_version_wrap(
        self: Versioned[P, Awaitable[T]],
        ref: VersionRef | str,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> Awaitable[TraceResult[T]]:
        """Run a specific version of an asynchronous function with trace wrapping."""
        ...

    def get_version(self) -> VersionId:
        """Get the current version identifier."""
        ...


class RemoteCap(Protocol[P, R], Traced[P, R]):
    """Protocol adding remote execution capabilities to a traced callable.

    Extends Traced with remote execution support, allowing functions to be
    executed on remote targets with automatic result handling.
    """

    @overload
    def execute_remote(
        self: RemoteCap[P, T], target: str, *args: P.args, **kwargs: P.kwargs
    ) -> Awaitable[T]:
        """Execute a synchronous function remotely."""
        ...

    @overload
    def execute_remote(
        self: RemoteCap[P, Awaitable[T]], target: str, *args: P.args, **kwargs: P.kwargs
    ) -> Awaitable[T]:
        """Execute an asynchronous function remotely."""
        ...

    @overload
    def execute_remote_wrap(
        self: RemoteCap[P, T], target: str, *args: P.args, **kwargs: P.kwargs
    ) -> Awaitable[TraceResult[T]]:
        """Execute a synchronous function remotely with trace wrapping."""
        ...

    @overload
    def execute_remote_wrap(
        self: RemoteCap[P, Awaitable[T]], target: str, *args: P.args, **kwargs: P.kwargs
    ) -> Awaitable[TraceResult[T]]:
        """Execute an asynchronous function remotely with trace wrapping."""
        ...


class TracedVersioned(Versioned[P, R], Protocol[P, R]):
    """Composition protocol for traced and versioned callables."""

    ...


class TracedRemote(RemoteCap[P, R], Protocol[P, R]):
    """Composition protocol for traced and remote-capable callables."""

    ...


class TracedVersionedRemote(Versioned[P, R], RemoteCap[P, R], Protocol[P, R]):
    """Composition protocol for traced, versioned, and remote-capable callables."""

    ...


from .versioning.types import VersionId, VersionRef