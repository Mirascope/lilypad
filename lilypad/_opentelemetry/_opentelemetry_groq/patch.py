"""OpenTelemetry patch for Groq."""

from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from typing import Any, ParamSpec, Protocol, cast, Union

from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from opentelemetry.semconv.attributes import error_attributes
from opentelemetry.trace import SpanKind, Status, StatusCode, Tracer
from opentelemetry.util.types import AttributeValue
from unittest.mock import AsyncMock

from lilypad._opentelemetry._opentelemetry_groq.utils import (
    GroqChunkHandler,
    GroqMetadata,
    default_groq_cleanup,
    set_message_event,
    set_response_attributes,
)
from lilypad._opentelemetry._utils import (
    AsyncStreamWrapper,
    StreamWrapper,
    set_server_address_and_port,
)


def get_llm_request_attributes(
    kwargs: dict[str, Any],
    client_instance: Any,
    operation_name: str = gen_ai_attributes.GenAiOperationNameValues.CHAT.value,
) -> dict[str, AttributeValue]:
    """Get LLM request attributes for Groq.

    Args:
        kwargs: The keyword arguments passed to the LLM request.
        client_instance: The Groq client instance.
        operation_name: The operation name. Defaults to "chat".

    Returns:
        A dictionary of LLM request attributes.
    """
    attributes = {
        gen_ai_attributes.GEN_AI_OPERATION_NAME: operation_name,
        gen_ai_attributes.GEN_AI_REQUEST_MODEL: kwargs.get("model"),
        gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE: kwargs.get("temperature"),
        gen_ai_attributes.GEN_AI_REQUEST_TOP_P: kwargs.get("top_p"),
        gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS: kwargs.get("max_tokens"),
        gen_ai_attributes.GEN_AI_SYSTEM: "groq",
    }
    set_server_address_and_port(client_instance, attributes)

    # filter out None values
    return {k: v for k, v in attributes.items() if v is not None}


P = ParamSpec("P")


class StreamProtocol(Protocol):
    """Protocol for synchronous streams."""

    def __iter__(self) -> Iterator[Any]:
        ...

    def __next__(self) -> Any:
        ...

    def close(self) -> None:
        ...


class AsyncStreamProtocol(Protocol):
    """Protocol for asynchronous streams."""

    def __aiter__(self) -> AsyncIterator[Any]:
        ...

    async def __anext__(self) -> Any:
        ...

    async def aclose(self) -> None:
        ...


def chat_completions_create(
    tracer: Tracer,
) -> Callable[[Callable[P, Any], Any, tuple[Any, ...], dict[str, Any]], Any]:
    """Create a traced chat completion.

    Args:
        tracer: The tracer to use.

    Returns:
        A wrapped function that creates a traced chat completion.
    """

    def traced_method(
        wrapped: Callable[P, Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any:
        span_attributes = {**get_llm_request_attributes(kwargs, instance)}

        span_name = f"{span_attributes[gen_ai_attributes.GEN_AI_OPERATION_NAME]} {span_attributes[gen_ai_attributes.GEN_AI_REQUEST_MODEL]}"
        with tracer.start_as_current_span(
            name=span_name,
            kind=SpanKind.CLIENT,
            attributes=span_attributes,
            end_on_exit=False,
        ) as span:
            if span.is_recording():
                for message in kwargs.get("messages", []):
                    set_message_event(span, message)
            try:
                result = wrapped(*args, **kwargs)
                if kwargs.get("stream", False):
                    # Convert list to iterator if necessary
                    if isinstance(result, list):
                        result = iter(result)

                    class WrappedStream(StreamProtocol):
                        """A wrapper for sync streams that ensures proper protocol implementation."""

                        def __init__(self) -> None:
                            """Initialize the stream wrapper."""
                            self._iterator = result

                        def __iter__(self) -> Iterator[Any]:
                            """Return self as an iterator."""
                            return self

                        def __next__(self) -> Any:
                            """Get the next item from the stream."""
                            return next(self._iterator)

                        def close(self) -> None:
                            """Close the stream if possible."""
                            if hasattr(self._iterator, "close"):
                                self._iterator.close()  # type: ignore

                    # Ensure stream implements required protocol
                    if not hasattr(result, "__iter__"):
                        result = WrappedStream()
                    elif not isinstance(result, WrappedStream):
                        # Wrap existing iterators to ensure consistent behavior
                        wrapped_stream = WrappedStream()
                        wrapped_stream._iterator = result
                        result = wrapped_stream

                    return StreamWrapper(
                        span=span,
                        stream=cast(StreamProtocol, result),
                        metadata=GroqMetadata(),
                        chunk_handler=GroqChunkHandler(),
                        cleanup_handler=default_groq_cleanup,
                    )

                # Handle non-streaming response
                if span.is_recording():
                    set_response_attributes(span, result)
                span.set_status(Status(StatusCode.OK))
                return result
            except Exception as e:
                if span.is_recording():
                    span.set_status(
                        Status(
                            StatusCode.ERROR,
                            str(e),
                        )
                    )
                    span.set_attributes(error_attributes(e))
                raise
            finally:
                span.end()

    return traced_method


def chat_completions_create_async(
    tracer: Tracer,
) -> Callable[[Callable[P, Any], Any, tuple[Any, ...], dict[str, Any]], Awaitable[Any]]:
    """Create an async traced chat completion.

    Args:
        tracer: The tracer to use.

    Returns:
        A wrapped async function that creates a traced chat completion.
    """

    async def traced_method(
        wrapped: Callable[P, Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any:
        span_attributes = {**get_llm_request_attributes(kwargs, instance)}

        span_name = f"{span_attributes[gen_ai_attributes.GEN_AI_OPERATION_NAME]} {span_attributes[gen_ai_attributes.GEN_AI_REQUEST_MODEL]}"
        with tracer.start_as_current_span(
            name=span_name,
            kind=SpanKind.CLIENT,
            attributes=span_attributes,
            end_on_exit=False,
        ) as span:
            if span.is_recording():
                for message in kwargs.get("messages", []):
                    set_message_event(span, message)
            try:
                result = await wrapped(*args, **kwargs)

                if kwargs.get("stream", False):
                    # Convert list to iterator if necessary
                    if isinstance(result, list):
                        result = iter(result)

                    class WrappedAsyncStream(AsyncStreamProtocol):
                        """A wrapper for async streams that ensures proper protocol implementation."""

                        def __init__(self) -> None:
                            """Initialize the async stream wrapper."""
                            self._iterator: Union[AsyncIterator[Any], Iterator[Any]] = result

                        def __aiter__(self) -> AsyncIterator[Any]:
                            """Return self as an async iterator."""
                            return self

                        async def __anext__(self) -> Any:
                            """Get the next item from the stream."""
                            try:
                                if isinstance(self._iterator, AsyncIterator):
                                    return await self._iterator.__anext__()
                                if isinstance(self._iterator, Iterator):
                                    try:
                                        return next(self._iterator)
                                    except StopIteration:
                                        raise StopAsyncIteration
                                # Handle async generators
                                if hasattr(self._iterator, "asend"):
                                    return await self._iterator.asend(None)  # type: ignore
                                raise StopAsyncIteration
                            except (StopIteration, StopAsyncIteration):
                                raise StopAsyncIteration

                        async def aclose(self) -> None:
                            """Close the async stream."""
                            if hasattr(self._iterator, "aclose"):
                                await self._iterator.aclose()  # type: ignore

                    # Ensure stream implements required protocol
                    if not hasattr(result, "__aiter__"):
                        result = WrappedAsyncStream()
                    elif not isinstance(result, WrappedAsyncStream):
                        # Wrap existing async iterators to ensure consistent behavior
                        wrapped_stream = WrappedAsyncStream()
                        wrapped_stream._iterator = result
                        result = wrapped_stream

                    return AsyncStreamWrapper(
                        span=span,
                        stream=cast(AsyncStreamProtocol, result),
                        metadata=GroqMetadata(),
                        chunk_handler=GroqChunkHandler(),
                        cleanup_handler=default_groq_cleanup,
                    )

                # Handle non-streaming response
                if span.is_recording():
                    set_response_attributes(span, result)
                span.set_status(Status(StatusCode.OK))
                return result
            except Exception as e:
                if span.is_recording():
                    span.set_status(
                        Status(
                            StatusCode.ERROR,
                            str(e),
                        )
                    )
                    span.set_attributes(error_attributes(e))
                raise  # Re-raise the original error without modification
            finally:
                span.end()

    return traced_method
