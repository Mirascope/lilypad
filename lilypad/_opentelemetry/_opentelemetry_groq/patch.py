"""OpenTelemetry patch for Groq."""

from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from typing import Any, ParamSpec, Protocol, cast

from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from opentelemetry.semconv.attributes import error_attributes
from opentelemetry.trace import SpanKind, Status, StatusCode, Tracer
from opentelemetry.util.types import AttributeValue

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
                    # Ensure stream implements required protocol
                    if not hasattr(result, "close"):
                        original_result = result

                        class WrappedStream(StreamProtocol):
                            def __init__(self) -> None:
                                self._iterator = iter(original_result)

                            def __iter__(self) -> Iterator[Any]:
                                return self

                            def __next__(self) -> Any:
                                return next(self._iterator)

                            def close(self) -> None:
                                if hasattr(self._iterator, "close"):
                                    self._iterator.close()

                        result = WrappedStream()
                    return StreamWrapper(
                        span=span,
                        stream=cast(StreamProtocol, result if isinstance(result, WrappedStream) else WrappedStream()),
                        metadata=GroqMetadata(),
                        chunk_handler=GroqChunkHandler(),
                        cleanup_handler=default_groq_cleanup,
                    )

                if span.is_recording():
                    set_response_attributes(span, result)
                span.end()
                return result

            except Exception as error:
                span.set_status(Status(StatusCode.ERROR, str(error)))
                if span.is_recording():
                    span.set_attribute(
                        error_attributes.ERROR_TYPE, type(error).__qualname__
                    )
                span.end()
                raise

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
                            self._iterator = result

                        def __aiter__(self) -> AsyncIterator[Any]:
                            """Return self as an async iterator."""
                            return self

                        async def __anext__(self) -> Any:
                            """Get the next item from the stream."""
                            try:
                                if hasattr(self._iterator, "__anext__"):
                                    # Handle native async iterators
                                    return await self._iterator.__anext__()
                                if hasattr(self._iterator, "__next__"):
                                    # Handle sync iterators
                                    try:
                                        return next(self._iterator)
                                    except StopIteration:
                                        raise StopAsyncIteration
                                # Handle async generators
                                if hasattr(self._iterator, "asend"):
                                    return await self._iterator.asend(None)
                                raise StopAsyncIteration
                            except (StopIteration, StopAsyncIteration):
                                raise StopAsyncIteration

                        async def aclose(self) -> None:
                            """Close the async stream."""
                            if hasattr(self._iterator, "aclose"):
                                await self._iterator.aclose()

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

                if span.is_recording():
                    set_response_attributes(span, result)
                span.end()
                return result

            except Exception as error:
                span.set_status(Status(StatusCode.ERROR, str(error)))
                if span.is_recording():
                    span.set_attribute(
                        error_attributes.ERROR_TYPE, type(error).__qualname__
                    )
                span.end()
                raise

    return traced_method
