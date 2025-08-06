from unittest.mock import Mock, AsyncMock
from typing import Any, Iterator, AsyncIterator
import pytest

from lilypad._internal.otel.utils import (
    StreamWrapper,
    AsyncStreamWrapper,
    ChoiceBuffer,
    ToolCallBuffer,
    StreamProtocol,
    AsyncStreamProtocol,
)
from lilypad._internal.otel.openai.utils import (
    OpenAIMetadata,
    OpenAIChunkHandler,
    default_openai_cleanup,
    set_message_event,
    set_response_attributes,
    get_tool_calls,
    get_choice_event,
)


def test_stream_wrapper_iteration():
    chunks = [
        Mock(
            id="1",
            model="gpt-4",
            choices=[
                Mock(
                    index=0,
                    delta=Mock(content="Hello", tool_calls=None),
                    finish_reason=None,
                )
            ],
        ),
        Mock(
            id="1",
            model="gpt-4",
            choices=[
                Mock(
                    index=0,
                    delta=Mock(content=" world", tool_calls=None),
                    finish_reason=None,
                )
            ],
        ),
        Mock(
            id="1",
            model="gpt-4",
            choices=[],
            usage=Mock(prompt_tokens=10, completion_tokens=20),
        ),
    ]

    span = Mock()
    span.is_recording.return_value = True
    stream = Mock()
    stream.__iter__ = Mock(return_value=iter(chunks))
    stream.__next__ = Mock(side_effect=chunks)
    stream.close = Mock()

    metadata = OpenAIMetadata()
    chunk_handler = OpenAIChunkHandler()
    cleanup_handler = default_openai_cleanup

    wrapper = StreamWrapper(span, stream, metadata, chunk_handler, cleanup_handler)

    collected_content = ""
    for chunk in wrapper:
        if hasattr(chunk, "choices") and chunk.choices:
            for choice in chunk.choices:
                if (
                    hasattr(choice, "delta")
                    and hasattr(choice.delta, "content")
                    and choice.delta.content
                ):
                    collected_content += choice.delta.content

    assert collected_content == "Hello world"
    span.set_attributes.assert_called()
    span.add_event.assert_called()
    span.end.assert_called_once()


def test_stream_wrapper_with_error():
    span = Mock()
    span.is_recording.return_value = True

    class ErrorStream(StreamProtocol):
        def __iter__(self) -> Iterator:
            return self

        def __next__(self) -> Any:
            raise Exception("Stream error")

        def close(self) -> None:
            pass

    stream = ErrorStream()
    metadata = OpenAIMetadata()
    chunk_handler = OpenAIChunkHandler()

    wrapper = StreamWrapper(span, stream, metadata, chunk_handler)

    with pytest.raises(Exception, match="Stream error"):
        for _ in wrapper:
            pass

    span.set_status.assert_called_once()
    span.set_attribute.assert_called()
    span.end.assert_called_once()


def test_stream_wrapper_span_not_recording():
    chunks = [
        Mock(
            id="1",
            model="gpt-4",
            choices=[
                Mock(
                    index=0,
                    delta=Mock(content="Hello", tool_calls=None),
                    finish_reason=None,
                )
            ],
        ),
        Mock(
            id="1",
            model="gpt-4",
            choices=[],
            usage=Mock(prompt_tokens=10, completion_tokens=20),
        ),
    ]

    span = Mock()
    span.is_recording.return_value = False

    class MockIterator(StreamProtocol):
        def __init__(self, items):
            self.items = items
            self.index = 0

        def __iter__(self) -> Iterator:
            return self

        def __next__(self) -> Any:
            if self.index >= len(self.items):
                raise StopIteration
            item = self.items[self.index]
            self.index += 1
            return item

        def close(self) -> None:
            pass

    stream = MockIterator(chunks)

    metadata = OpenAIMetadata()
    chunk_handler = OpenAIChunkHandler()

    wrapper = StreamWrapper(span, stream, metadata, chunk_handler)

    list(wrapper)

    span.add_event.assert_not_called()
    span.end.assert_called_once()


def test_stream_wrapper_context_manager():
    chunks = [
        Mock(
            id="1",
            model="gpt-4",
            choices=[
                Mock(
                    index=0,
                    delta=Mock(content="Hello", tool_calls=None),
                    finish_reason="stop",
                )
            ],
        ),
    ]

    span = Mock()
    span.is_recording.return_value = True

    class MockIterator(StreamProtocol):
        def __init__(self, items):
            self.items = items
            self.index = 0

        def __iter__(self) -> Iterator:
            return self

        def __next__(self) -> Any:
            if self.index >= len(self.items):
                raise StopIteration
            item = self.items[self.index]
            self.index += 1
            return item

        def close(self) -> None:
            pass

    stream = MockIterator(chunks)

    metadata = OpenAIMetadata()
    chunk_handler = OpenAIChunkHandler()
    cleanup_handler = default_openai_cleanup

    wrapper = StreamWrapper(span, stream, metadata, chunk_handler, cleanup_handler)

    with wrapper as w:
        list(w)

    span.end.assert_called_once()


def test_stream_wrapper_context_manager_with_error():
    span = Mock()
    span.is_recording.return_value = True

    class ErrorStream(StreamProtocol):
        def __iter__(self) -> Iterator:
            return self

        def __next__(self) -> Any:
            raise Exception("Stream error")

        def close(self) -> None:
            pass

    stream = ErrorStream()
    metadata = OpenAIMetadata()
    chunk_handler = OpenAIChunkHandler()

    wrapper = StreamWrapper(span, stream, metadata, chunk_handler)

    raised = False
    try:
        with wrapper as w:
            list(w)
    except Exception as e:
        raised = True
        assert str(e) == "Stream error"

    assert raised

    assert span.set_status.call_count >= 1
    span.set_attribute.assert_called()
    span.end.assert_called_once()


@pytest.mark.asyncio
async def test_stream_wrapper_close():
    span = Mock()
    span.is_recording.return_value = True

    stream = Mock()
    stream.close = Mock()

    metadata = OpenAIMetadata()
    chunk_handler = OpenAIChunkHandler()

    wrapper = StreamWrapper(span, stream, metadata, chunk_handler)

    await wrapper.close()

    stream.close.assert_called_once()
    span.end.assert_called_once()


def test_stream_wrapper_no_usage_info():
    chunks = [
        Mock(
            id="1",
            model="gpt-4",
            choices=[
                Mock(
                    index=0,
                    delta=Mock(content="Hello", tool_calls=None),
                    finish_reason="stop",
                )
            ],
        ),
        Mock(id="1", model="gpt-4", choices=[], usage=None),
    ]

    span = Mock()
    span.is_recording.return_value = True

    class MockIterator(StreamProtocol):
        def __init__(self, items):
            self.items = items
            self.index = 0

        def __iter__(self) -> Iterator:
            return self

        def __next__(self) -> Any:
            if self.index >= len(self.items):
                raise StopIteration
            item = self.items[self.index]
            self.index += 1
            return item

        def close(self) -> None:
            pass

    stream = MockIterator(chunks)

    metadata = OpenAIMetadata()
    chunk_handler = OpenAIChunkHandler()
    cleanup_handler = default_openai_cleanup

    wrapper = StreamWrapper(span, stream, metadata, chunk_handler, cleanup_handler)
    list(wrapper)

    span.set_attributes.assert_called()
    attributes = span.set_attributes.call_args[0][0]
    assert attributes["gen_ai.response.id"] == "1"
    assert attributes["gen_ai.response.model"] == "gpt-4"


@pytest.mark.asyncio
async def test_async_stream_wrapper_iteration():
    chunks = [
        Mock(
            id="1",
            model="gpt-4",
            choices=[
                Mock(
                    index=0,
                    delta=Mock(content="Hello", tool_calls=None),
                    finish_reason=None,
                )
            ],
        ),
        Mock(
            id="1",
            model="gpt-4",
            choices=[
                Mock(
                    index=0,
                    delta=Mock(content=" world", tool_calls=None),
                    finish_reason=None,
                )
            ],
        ),
        Mock(
            id="1",
            model="gpt-4",
            choices=[],
            usage=Mock(prompt_tokens=10, completion_tokens=20),
        ),
    ]

    class AsyncMockStream(AsyncStreamProtocol):
        def __init__(self, chunks):
            self.chunks = chunks
            self.index = 0

        def __aiter__(self) -> AsyncIterator:
            return self

        async def __anext__(self) -> Any:
            if self.index >= len(self.chunks):
                raise StopAsyncIteration
            chunk = self.chunks[self.index]
            self.index += 1
            return chunk

        async def aclose(self) -> None:
            pass

    span = Mock()
    span.is_recording.return_value = True
    stream = AsyncMockStream(chunks)

    metadata = OpenAIMetadata()
    chunk_handler = OpenAIChunkHandler()
    cleanup_handler = default_openai_cleanup

    wrapper = AsyncStreamWrapper(span, stream, metadata, chunk_handler, cleanup_handler)

    collected_content = ""
    async for chunk in wrapper:
        if hasattr(chunk, "choices") and chunk.choices:
            for choice in chunk.choices:
                if (
                    hasattr(choice, "delta")
                    and hasattr(choice.delta, "content")
                    and choice.delta.content
                ):
                    collected_content += choice.delta.content

    assert collected_content == "Hello world"
    span.set_attributes.assert_called()
    span.add_event.assert_called()
    span.end.assert_called_once()


@pytest.mark.asyncio
async def test_async_stream_wrapper_with_error():
    class AsyncErrorStream(AsyncStreamProtocol):
        def __aiter__(self) -> AsyncIterator:
            return self

        async def __anext__(self) -> Any:
            raise Exception("Async stream error")

        async def aclose(self) -> None:
            pass

    span = Mock()
    span.is_recording.return_value = True
    stream = AsyncErrorStream()

    metadata = OpenAIMetadata()
    chunk_handler = OpenAIChunkHandler()

    wrapper = AsyncStreamWrapper(span, stream, metadata, chunk_handler)

    with pytest.raises(Exception, match="Async stream error"):
        async for _ in wrapper:
            pass

    span.set_status.assert_called_once()
    span.set_attribute.assert_called()
    span.end.assert_called_once()


@pytest.mark.asyncio
async def test_async_stream_wrapper_context_manager():
    chunks = [
        Mock(
            id="1",
            model="gpt-4",
            choices=[
                Mock(
                    index=0,
                    delta=Mock(content="Hello", tool_calls=None),
                    finish_reason="stop",
                )
            ],
        ),
    ]

    class AsyncMockStream(AsyncStreamProtocol):
        def __init__(self, chunks):
            self.chunks = chunks
            self.index = 0

        def __aiter__(self) -> AsyncIterator:
            return self

        async def __anext__(self) -> Any:
            if self.index >= len(self.chunks):
                raise StopAsyncIteration
            chunk = self.chunks[self.index]
            self.index += 1
            return chunk

        async def aclose(self) -> None:
            pass

    span = Mock()
    span.is_recording.return_value = True
    stream = AsyncMockStream(chunks)

    metadata = OpenAIMetadata()
    chunk_handler = OpenAIChunkHandler()
    cleanup_handler = default_openai_cleanup

    wrapper = AsyncStreamWrapper(span, stream, metadata, chunk_handler, cleanup_handler)

    async with wrapper as w:
        [chunk async for chunk in w]

    span.end.assert_called_once()


@pytest.mark.asyncio
async def test_async_stream_wrapper_context_manager_with_error():
    span = Mock()
    span.is_recording.return_value = True

    class AsyncErrorStream(AsyncStreamProtocol):
        def __aiter__(self) -> AsyncIterator:
            return self

        async def __anext__(self) -> Any:
            raise Exception("Async stream error")

        async def aclose(self) -> None:
            pass

    stream = AsyncErrorStream()
    metadata = OpenAIMetadata()
    chunk_handler = OpenAIChunkHandler()

    wrapper = AsyncStreamWrapper(span, stream, metadata, chunk_handler)

    raised = False
    try:
        async with wrapper as w:
            [chunk async for chunk in w]
    except Exception as e:
        raised = True
        assert str(e) == "Async stream error"

    assert raised

    assert span.set_status.call_count >= 1
    span.set_attribute.assert_called()
    span.end.assert_called_once()


@pytest.mark.asyncio
async def test_async_stream_wrapper_close():
    span = Mock()
    span.is_recording.return_value = True

    stream = AsyncMock()
    stream.aclose = AsyncMock()

    metadata = OpenAIMetadata()
    chunk_handler = OpenAIChunkHandler()

    wrapper = AsyncStreamWrapper(span, stream, metadata, chunk_handler)

    await wrapper.close()

    stream.aclose.assert_called_once()
    span.end.assert_called_once()


@pytest.mark.asyncio
async def test_async_stream_wrapper_span_not_recording():
    chunks = [
        Mock(
            id="1",
            model="gpt-4",
            choices=[
                Mock(
                    index=0,
                    delta=Mock(content="Hello", tool_calls=None),
                    finish_reason=None,
                )
            ],
        ),
        Mock(
            id="1",
            model="gpt-4",
            choices=[],
            usage=Mock(prompt_tokens=10, completion_tokens=20),
        ),
    ]

    class AsyncMockStream(AsyncStreamProtocol):
        def __init__(self, chunks):
            self.chunks = chunks
            self.index = 0

        def __aiter__(self) -> AsyncIterator:
            return self

        async def __anext__(self) -> Any:
            if self.index >= len(self.chunks):
                raise StopAsyncIteration
            chunk = self.chunks[self.index]
            self.index += 1
            return chunk

        async def aclose(self) -> None:
            pass

    span = Mock()
    span.is_recording.return_value = False
    stream = AsyncMockStream(chunks)

    metadata = OpenAIMetadata()
    chunk_handler = OpenAIChunkHandler()

    wrapper = AsyncStreamWrapper(span, stream, metadata, chunk_handler)

    async for _ in wrapper:
        pass

    span.add_event.assert_not_called()
    span.end.assert_called_once()


def test_extract_metadata_basic():
    handler = OpenAIChunkHandler()
    metadata: OpenAIMetadata = {}
    chunk = Mock(
        model="gpt-4",
        id="test-id",
        service_tier="default",
        usage=Mock(completion_tokens=10, prompt_tokens=5),
    )

    handler.extract_metadata(chunk, metadata)

    assert metadata.get("response_model") == "gpt-4"
    assert metadata.get("response_id") == "test-id"
    assert metadata.get("service_tier") == "default"
    assert metadata.get("completion_tokens") == 10
    assert metadata.get("prompt_tokens") == 5


def test_extract_metadata_partial():
    handler = OpenAIChunkHandler()
    metadata: OpenAIMetadata = {"response_model": "existing-model"}
    chunk = Mock(spec=["id"])
    chunk.id = "test-id"

    handler.extract_metadata(chunk, metadata)

    assert metadata.get("response_model") == "existing-model"
    assert metadata.get("response_id") == "test-id"


def test_process_chunk():
    handler = OpenAIChunkHandler()
    buffers = []

    chunk = Mock(
        choices=[
            Mock(
                index=0,
                delta=Mock(content="Hello", tool_calls=None),
                finish_reason="stop",
            )
        ]
    )

    handler.process_chunk(chunk, buffers)

    assert len(buffers) == 1
    assert buffers[0].finish_reason == "stop"
    assert buffers[0].text_content == ["Hello"]


def test_process_chunk_no_choices():
    handler = OpenAIChunkHandler()
    buffers = []

    chunk = Mock(spec=[])

    handler.process_chunk(chunk, buffers)

    assert len(buffers) == 0


def test_process_chunk_no_delta():
    handler = OpenAIChunkHandler()
    buffers = []

    chunk = Mock(choices=[Mock(index=0, delta=None, finish_reason=None)])

    handler.process_chunk(chunk, buffers)

    assert len(buffers) == 0


def test_process_chunk_with_tool_calls():
    handler = OpenAIChunkHandler()
    buffers = []

    tool_call = Mock()
    tool_call.index = 0
    tool_call.id = "call_123"
    tool_call.function = Mock()
    tool_call.function.name = "test_func"
    tool_call.function.arguments = '{"arg": "value"}'

    chunk = Mock(
        choices=[
            Mock(
                index=0,
                delta=Mock(content=None, tool_calls=[tool_call]),
                finish_reason=None,
            )
        ]
    )

    handler.process_chunk(chunk, buffers)

    assert len(buffers) == 1
    assert len(buffers[0].tool_calls_buffers) == 1
    assert buffers[0].tool_calls_buffers[0].function_name == "test_func"


def test_set_response_attributes_basic():
    span = Mock()

    response = Mock(spec=["id", "model", "service_tier", "usage", "choices"])
    response.id = "test-id"
    response.model = "gpt-4"
    response.service_tier = "default"
    response.usage = Mock(prompt_tokens=10, completion_tokens=20)
    choice = Mock(spec=["index", "finish_reason", "message"])
    choice.index = 0
    choice.finish_reason = "stop"
    choice.message = Mock(spec=["role", "content", "get", "tool_calls"])
    choice.message.role = "assistant"
    choice.message.content = "Hello world"
    choice.message.get = Mock(return_value=None)
    choice.message.tool_calls = None
    response.choices = [choice]

    set_response_attributes(span, response)

    span.set_attributes.assert_called_once()
    attributes = span.set_attributes.call_args[0][0]

    assert attributes["gen_ai.response.id"] == "test-id"
    assert attributes["gen_ai.response.model"] == "gpt-4"
    assert attributes["gen_ai.openai.request.service_tier"] == "default"
    assert attributes["gen_ai.usage.input_tokens"] == 10
    assert attributes["gen_ai.usage.output_tokens"] == 20
    assert attributes["gen_ai.response.finish_reasons"] == ["stop"]

    span.add_event.assert_called()


def test_set_response_attributes_no_usage():
    span = Mock()

    response = Mock(spec=["id", "model", "choices"])
    response.id = "test-id"
    response.model = "gpt-4"
    response.choices = []

    set_response_attributes(span, response)

    span.set_attributes.assert_called_once()
    attributes = span.set_attributes.call_args[0][0]

    assert attributes["gen_ai.response.id"] == "test-id"
    assert attributes["gen_ai.response.model"] == "gpt-4"
    assert "gen_ai.usage.input_tokens" not in attributes
    assert "gen_ai.usage.output_tokens" not in attributes


def test_get_tool_calls_from_dict():
    message = {
        "tool_calls": [
            {
                "id": "call_123",
                "type": "function",
                "function": {"name": "test_func", "arguments": '{"arg": "value"}'},
            }
        ]
    }

    result = get_tool_calls(message)

    assert result is not None
    assert len(result) == 1
    assert result[0]["id"] == "call_123"
    assert result[0]["type"] == "function"
    assert result[0]["function"]["name"] == "test_func"
    assert result[0]["function"]["arguments"] == '{"arg": "value"}'


def test_get_tool_calls_none():
    message = {"content": "Hello"}
    result = get_tool_calls(message)
    assert result is None


def test_get_tool_calls_from_base_model():
    from pydantic import BaseModel

    class FunctionModel(BaseModel):
        name: str = "test_func"
        arguments: str = "{}"

        def model_dump(
            self,
            *,
            mode=None,
            include=None,
            exclude=None,
            context=None,
            by_alias: bool | None = False,
            exclude_unset=False,
            exclude_defaults=False,
            exclude_none=False,
            **kwargs,
        ):
            return {"name": self.name, "arguments": self.arguments}

    class ToolCallModel(BaseModel):
        id: str
        type: str
        function: FunctionModel

    tool_call = ToolCallModel(id="call_123", type="function", function=FunctionModel())

    message = Mock()
    message.tool_calls = [tool_call]
    message.get = Mock(return_value=[tool_call])

    result = get_tool_calls(message)

    assert result is not None
    assert len(result) == 1
    assert result[0]["id"] == "call_123"
    assert result[0]["type"] == "function"
    assert result[0]["function"]["name"] == "test_func"


def test_default_openai_cleanup_basic():
    span = Mock()
    metadata: OpenAIMetadata = {
        "response_model": "gpt-4",
        "response_id": "test-id",
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "service_tier": "default",
        "finish_reasons": ["stop"],
    }
    buffers = [ChoiceBuffer(0)]
    buffers[0].text_content = ["Hello", " world"]
    buffers[0].finish_reason = "stop"

    default_openai_cleanup(span, metadata, buffers)

    span.set_attributes.assert_called_once()
    attributes = span.set_attributes.call_args[0][0]
    assert attributes["gen_ai.response.model"] == "gpt-4"
    assert attributes["gen_ai.response.id"] == "test-id"
    assert attributes["gen_ai.usage.input_tokens"] == 10
    assert attributes["gen_ai.usage.output_tokens"] == 20

    span.add_event.assert_called_once()
    event_call = span.add_event.call_args
    assert event_call[0][0] == "gen_ai.choice"
    assert '"content": "Hello world"' in event_call[1]["attributes"]["message"]


def test_default_openai_cleanup_with_tool_calls():
    span = Mock()
    metadata: OpenAIMetadata = {}
    buffers = [ChoiceBuffer(0)]

    tool_call_buffer = ToolCallBuffer(0, "call_123", "test_func")
    tool_call_buffer.append_arguments('{"arg": ')
    tool_call_buffer.append_arguments('"value"}')
    buffers[0].tool_calls_buffers = [tool_call_buffer]

    default_openai_cleanup(span, metadata, buffers)

    span.add_event.assert_called_once()
    event_call = span.add_event.call_args
    assert '"tool_calls"' in event_call[1]["attributes"]["message"]


def test_default_openai_cleanup_with_none_tool_calls():
    span = Mock()
    metadata: OpenAIMetadata = {}
    buffers = [ChoiceBuffer(0)]

    tool_call_buffer = ToolCallBuffer(0, "call_123", "test_func")
    tool_call_buffer.append_arguments('{"arg": "value"}')
    buffers[0].tool_calls_buffers = [None, tool_call_buffer, None]

    default_openai_cleanup(span, metadata, buffers)

    span.add_event.assert_called_once()
    event_call = span.add_event.call_args
    message_str = event_call[1]["attributes"]["message"]
    import json

    message_data = json.loads(message_str)
    assert "tool_calls" in message_data
    assert (
        len(message_data["tool_calls"]) == 1
    )  # Only one valid tool call (Nones are skipped)
    assert message_data["tool_calls"][0]["id"] == "call_123"


def test_get_choice_event_with_message():
    choice = Mock()
    choice.index = 0
    choice.finish_reason = "stop"
    choice.message = Mock(spec=["role", "content", "get", "tool_calls"])
    choice.message.role = "assistant"
    choice.message.content = "Hello"
    choice.message.get = Mock(return_value=None)
    choice.message.tool_calls = None

    result = get_choice_event(choice)

    assert result["gen_ai.system"] == "openai"
    assert result["index"] == 0
    assert result["finish_reason"] == "stop"
    assert '"content":"Hello"' in str(result["message"])


def test_get_choice_event_with_tool_calls():
    choice = Mock()
    choice.index = 0
    choice.finish_reason = "stop"
    choice.message = Mock(spec=["role", "content", "get", "tool_calls"])
    choice.message.role = "assistant"
    choice.message.content = None
    choice.message.tool_calls = [
        {"id": "call_123", "type": "function", "function": {"name": "test"}}
    ]
    choice.message.get = Mock(
        return_value=[
            {"id": "call_123", "type": "function", "function": {"name": "test"}}
        ]
    )

    result = get_choice_event(choice)

    assert result["gen_ai.system"] == "openai"
    assert result["index"] == 0
    assert result["finish_reason"] == "stop"
    assert '"tool_calls"' in str(result["message"])


def test_set_message_event_with_content():
    span = Mock()
    message = {"role": "user", "content": "Hello"}

    set_message_event(span, message)

    span.add_event.assert_called_once_with(
        "gen_ai.user.message",
        attributes={"gen_ai.system": "openai", "content": "Hello"},
    )


def test_set_message_event_with_non_string_content():
    span = Mock()
    message = {"role": "user", "content": {"type": "text", "text": "Hello"}}

    set_message_event(span, message)

    span.add_event.assert_called_once()
    attributes = span.add_event.call_args[1]["attributes"]
    assert attributes["content"] == '{"type":"text","text":"Hello"}'


def test_set_message_event_with_tool_calls():
    span = Mock()
    message = {
        "role": "assistant",
        "tool_calls": [
            {
                "id": "call_123",
                "type": "function",
                "function": {"name": "test_func", "arguments": "{}"},
            }
        ],
    }

    set_message_event(span, message)

    span.add_event.assert_called_once()
    call_args = span.add_event.call_args
    assert call_args[0][0] == "gen_ai.assistant.message"
    assert "tool_calls" in call_args[1]["attributes"]


def test_set_message_event_tool_response():
    span = Mock()
    message = {"role": "tool", "tool_call_id": "call_123", "content": "Result"}

    set_message_event(span, message)

    span.add_event.assert_called_once()
    call_args = span.add_event.call_args
    assert call_args[0][0] == "gen_ai.tool.message"
    assert call_args[1]["attributes"]["content"] == "Result"


def test_set_message_event_tool_response_no_content():
    span = Mock()
    message = {"role": "tool", "tool_call_id": "call_123"}

    set_message_event(span, message)

    span.add_event.assert_called_once()
    call_args = span.add_event.call_args
    assert call_args[0][0] == "gen_ai.tool.message"
    assert call_args[1]["attributes"]["id"] == "call_123"


def test_set_message_event_tool_without_id():
    span = Mock()
    message = {"role": "tool"}

    set_message_event(span, message)

    span.add_event.assert_called_once()
    call_args = span.add_event.call_args
    assert call_args[0][0] == "gen_ai.tool.message"
    assert "id" not in call_args[1]["attributes"]


def test_get_tool_calls_without_function():
    message = {
        "tool_calls": [
            {
                "id": "call_123",
                "type": "function",
            }
        ]
    }

    result = get_tool_calls(message)

    assert result is not None
    assert len(result) == 1
    assert result[0]["id"] == "call_123"
    assert result[0]["type"] == "function"
    assert "function" not in result[0]


def test_get_tool_calls_function_without_name():
    message = {
        "tool_calls": [
            {
                "id": "call_123",
                "type": "function",
                "function": {"arguments": '{"arg": "value"}'},
            }
        ]
    }

    result = get_tool_calls(message)

    assert result is not None
    assert len(result) == 1
    assert result[0]["id"] == "call_123"
    assert result[0]["type"] == "function"
    assert result[0]["function"]["arguments"] == '{"arg": "value"}'
    assert "name" not in result[0]["function"]


def test_get_choice_event_without_message():
    choice = Mock()
    choice.message = None

    result = get_choice_event(choice)

    assert result["gen_ai.system"] == "openai"
    assert "message" not in result
    assert "index" not in result
    assert "finish_reason" not in result


def test_set_response_attributes_without_id():
    from lilypad._internal.otel.openai.utils import set_response_attributes

    span = Mock()
    response = Mock()
    response.model = "gpt-4"
    response.id = None
    response.service_tier = None
    response.choices = []

    set_response_attributes(span, response)

    attributes = span.set_attributes.call_args[0][0]
    assert attributes["gen_ai.response.model"] == "gpt-4"
    assert "gen_ai.response.id" not in attributes
