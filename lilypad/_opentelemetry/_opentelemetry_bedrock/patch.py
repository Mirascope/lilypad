from opentelemetry.semconv.attributes import error_attributes
from opentelemetry.trace import Status, StatusCode, Tracer
from typing_extensions import ParamSpec

P = ParamSpec("P")

from botocore.eventstream import EventStream
from mypy_boto3_bedrock_runtime.type_defs import ConverseStreamOutputTypeDef

from lilypad._opentelemetry._utils import AsyncStreamWrapper, StreamWrapper

from .utils import (
    BedrockChunkHandler,
    BedrockMetadata,
    default_bedrock_cleanup,
    get_bedrock_llm_request_attributes,
)


class SyncEventStreamAdapter:
    """Convert EventStream into a Python iterator.
    Assuming EventStream itself is iterable:
    If not, fallback to read loop.
    """
    def __init__(self, event_stream: "EventStream[ConverseStreamOutputTypeDef]"):
        self._iter = iter(event_stream)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._iter)


class AsyncEventStreamAdapter:
    """Convert EventStream into an async iterator.
    """
    def __init__(self, event_stream: "EventStream[ConverseStreamOutputTypeDef]"):
        self.event_stream = event_stream
        self._iter = None

    def __aiter__(self):
        return self._async_iter()

    async def _async_iter(self):
        async for chunk in self.event_stream:
            yield chunk

def make_api_call_patch(tracer: Tracer):
    def wrapper(wrapped, instance, args, kwargs):
        operation_name, params = args
        service_name = instance.meta.service_model.service_name
        if service_name == "bedrock-runtime":
            span_attributes = get_bedrock_llm_request_attributes(params, instance)
            if operation_name == "Converse":
                # Non-stream sync call
                span_name = f"chat {span_attributes.get('gen_ai.request.model','unknown')}"
                with tracer.start_as_current_span(name=span_name, end_on_exit=False) as span:
                    try:
                        result = wrapped(*args, **kwargs)
                        default_bedrock_cleanup(span, BedrockMetadata(), [])
                        span.end()
                        return result
                    except Exception as error:
                        span.set_status(Status(StatusCode.ERROR, str(error)))
                        if span.is_recording():
                            span.set_attribute(error_attributes.ERROR_TYPE, type(error).__qualname__)
                        span.end()
                        raise
            elif operation_name == "ConverseStream":
                # Streaming sync call
                span_name = f"chat_stream {span_attributes.get('gen_ai.request.model','unknown')}"
                with tracer.start_as_current_span(name=span_name, end_on_exit=False) as span:
                    try:
                        response = wrapped(*args, **kwargs)
                        if "stream" in response:
                            event_stream = response["stream"]
                            # event_stream is EventStream[ConverseStreamOutputTypeDef]
                            adapted_stream = SyncEventStreamAdapter(event_stream)
                            metadata = BedrockMetadata()
                            chunk_handler = BedrockChunkHandler()
                            response["stream"] = StreamWrapper(
                                span=span,
                                stream=adapted_stream,
                                metadata=metadata,
                                chunk_handler=chunk_handler,
                                cleanup_handler=default_bedrock_cleanup,
                            )
                        else:
                            default_bedrock_cleanup(span, BedrockMetadata(), [])
                            span.end()
                        return response
                    except Exception as error:
                        span.set_status(Status(StatusCode.ERROR, str(error)))
                        if span.is_recording():
                            span.set_attribute(error_attributes.ERROR_TYPE, type(error).__qualname__)
                        span.end()
                        raise
            else:
                return wrapped(*args, **kwargs)
        else:
            return wrapped(*args, **kwargs)
    return wrapper


def make_api_call_async_patch(tracer: Tracer):
    async def wrapper(wrapped, instance, args, kwargs):
        operation_name, params = args
        service_name = instance.meta.service_model.service_name
        if service_name == "bedrock-runtime":
            span_attributes = get_bedrock_llm_request_attributes(params, instance)
            if operation_name == "Converse":
                # Non-stream async call
                span_name = f"chat {span_attributes.get('gen_ai.request.model','unknown')}"
                with tracer.start_as_current_span(name=span_name, end_on_exit=False) as span:
                    try:
                        response = await wrapped(*args, **kwargs)
                        default_bedrock_cleanup(span, BedrockMetadata(), [])
                        span.end()
                        return response
                    except Exception as error:
                        span.set_status(Status(StatusCode.ERROR, str(error)))
                        if span.is_recording():
                            span.set_attribute(error_attributes.ERROR_TYPE, type(error).__qualname__)
                        span.end()
                        raise
            elif operation_name == "ConverseStream":
                # Streaming async call
                span_name = f"chat_stream {span_attributes.get('gen_ai.request.model','unknown')}"
                with tracer.start_as_current_span(name=span_name, end_on_exit=False) as span:
                    try:
                        response = await wrapped(*args, **kwargs)
                        if "stream" in response:
                            event_stream = response["stream"]
                            adapted_stream = AsyncEventStreamAdapter(event_stream)
                            metadata = BedrockMetadata()
                            chunk_handler = BedrockChunkHandler()
                            response["stream"] = AsyncStreamWrapper(
                                span=span,
                                stream=adapted_stream,
                                metadata=metadata,
                                chunk_handler=chunk_handler,
                                cleanup_handler=default_bedrock_cleanup,
                            )
                        else:
                            default_bedrock_cleanup(span, BedrockMetadata(), [])
                            span.end()
                        return response
                    except Exception as error:
                        span.set_status(Status(StatusCode.ERROR, str(error)))
                        if span.is_recording():
                            span.set_attribute(error_attributes.ERROR_TYPE, type(error).__qualname__)
                        span.end()
                        raise
            else:
                return await wrapped(*args, **kwargs)
        else:
            return await wrapped(*args, **kwargs)
    return wrapper
