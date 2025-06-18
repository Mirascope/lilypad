from unittest.mock import Mock, MagicMock

import pytest
from opentelemetry.trace import StatusCode
from botocore.eventstream import EventStream

from lilypad._opentelemetry._opentelemetry_bedrock.patch import (
    make_api_call_patch,
    make_api_call_async_patch,
    AsyncEventStreamAdapter,
    SyncEventStreamAdapter,
)


@pytest.fixture
def mock_span():
    span = Mock()
    span.is_recording.return_value = True
    return span


@pytest.fixture
def mock_tracer(mock_span):
    tracer = Mock()

    def start_as_current_span(*args, **kwargs):
        class CM:
            def __enter__(self):
                return mock_span

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        return CM()

    tracer.start_as_current_span.side_effect = start_as_current_span
    return tracer


def test_make_api_call_patch_converse_success(mock_tracer, mock_span):
    patcher = make_api_call_patch(mock_tracer)
    wrapped = Mock()
    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"
    kwargs = {"modelId": "test-model"}
    args = ("Converse", kwargs)
    wrapped.return_value = {"non_stream_result": True}

    result = patcher(wrapped, instance, args, {})
    assert result == {"non_stream_result": True}
    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.end.assert_called_once()
    mock_span.set_status.assert_not_called()


def test_make_api_call_patch_converse_stream_success(mock_tracer, mock_span):
    patcher = make_api_call_patch(mock_tracer)
    wrapped = Mock()
    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"

    fake_stream = MagicMock(spec=EventStream)
    fake_stream.__iter__.return_value = iter(["chunk1", "chunk2"])

    kwargs = {
        "modelId": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
    }
    args = ("ConverseStream", kwargs)
    wrapped.return_value = {"stream": fake_stream}

    result = patcher(wrapped, instance, args, {})
    assert "stream" in result
    stream_wrapper = result["stream"]
    chunks = list(stream_wrapper)
    assert chunks == ["chunk1", "chunk2"]
    mock_tracer.start_as_current_span.assert_called_once()


def test_make_api_call_patch_converse_error(mock_tracer, mock_span):
    patcher = make_api_call_patch(mock_tracer)
    wrapped = Mock(side_effect=Exception("test error"))
    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"
    kwargs = {"modelId": "test-model"}
    args = ("Converse", kwargs)

    with pytest.raises(Exception, match="test error"):
        patcher(wrapped, instance, args, {})

    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.set_status.assert_called()
    status_arg = mock_span.set_status.call_args[0][0]
    assert status_arg.status_code == StatusCode.ERROR
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_make_api_call_async_patch_converse_success(mock_tracer, mock_span):
    patcher = make_api_call_async_patch(mock_tracer)
    wrapped = Mock()

    async def async_mock(*_args, **_kwargs):
        return {"non_stream_async": True}

    wrapped.side_effect = async_mock

    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"
    kwargs = {"modelId": "test-model"}
    args = ("Converse", kwargs)
    resp = await patcher(wrapped, instance, args, {})
    assert resp == {"non_stream_async": True}
    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_make_api_call_async_patch_converse_stream_success(mock_tracer, mock_span):
    patcher = make_api_call_async_patch(mock_tracer)
    wrapped = Mock()

    async def async_mock(*_args, **_kwargs):
        fake_stream = MagicMock()
        fake_stream.__anext__.side_effect = ["chunkA", "chunkB", StopAsyncIteration]
        return {"stream": fake_stream}

    wrapped.side_effect = async_mock

    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"
    kwargs = {
        "modelId": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
    }
    args = ("ConverseStream", kwargs)

    resp = await patcher(wrapped, instance, args, {})
    assert "stream" in resp
    stream_wrapper = resp["stream"]

    collected = []
    async for c in stream_wrapper:
        collected.append(c)
    assert collected == ["chunkA", "chunkB"]
    mock_tracer.start_as_current_span.assert_called_once()


@pytest.mark.asyncio
async def test_make_api_call_async_patch_converse_error(mock_tracer, mock_span):
    patcher = make_api_call_async_patch(mock_tracer)
    wrapped = Mock()

    async def raise_error(*_args, **_kwargs):
        raise Exception("async error")

    wrapped.side_effect = raise_error

    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"
    kwargs = {"modelId": "test-model"}
    args = ("Converse", kwargs)

    with pytest.raises(Exception, match="async error"):
        await patcher(wrapped, instance, args, {})

    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.set_status.assert_called_once()
    status_arg = mock_span.set_status.call_args[0][0]
    assert status_arg.status_code == StatusCode.ERROR
    mock_span.end.assert_called_once()


def test_make_api_call_patch_non_bedrock_service(mock_tracer):
    """Test that non-bedrock-runtime services are passed through."""
    patcher = make_api_call_patch(mock_tracer)
    wrapped = Mock()
    instance = Mock()
    instance.meta.service_model.service_name = "s3"  # Not bedrock-runtime
    kwargs = {"Key": "test-key"}
    args = ("GetObject", kwargs)
    wrapped.return_value = {"Body": "test-data"}

    result = patcher(wrapped, instance, args, {})
    assert result == {"Body": "test-data"}
    mock_tracer.start_as_current_span.assert_not_called()  # Should not start span


@pytest.mark.asyncio
async def test_make_api_call_async_patch_non_bedrock_service(mock_tracer):
    """Test that non-bedrock-runtime services are passed through in async."""
    patcher = make_api_call_async_patch(mock_tracer)
    wrapped = Mock()

    async def async_mock(*_args, **_kwargs):
        return {"async_result": True}

    wrapped.side_effect = async_mock

    instance = Mock()
    instance.meta.service_model.service_name = "lambda"  # Not bedrock-runtime
    kwargs = {"FunctionName": "test-function"}
    args = ("Invoke", kwargs)

    result = await patcher(wrapped, instance, args, {})
    assert result == {"async_result": True}
    mock_tracer.start_as_current_span.assert_not_called()  # Should not start span


@pytest.mark.asyncio
async def test_async_event_stream_adapter_exception():
    """Test AsyncEventStreamAdapter exception handling."""
    from unittest.mock import AsyncMock

    mock_stream = AsyncMock()

    # Configure the mock to raise an exception
    mock_stream.__anext__.side_effect = ValueError("Stream error")

    adapter = AsyncEventStreamAdapter(mock_stream)

    with pytest.raises(ValueError, match="Stream error"):
        await adapter.__anext__()


@pytest.mark.asyncio
async def test_async_event_stream_adapter_stop_iteration():
    """Test AsyncEventStreamAdapter StopAsyncIteration handling."""
    from unittest.mock import AsyncMock

    mock_stream = AsyncMock()
    mock_stream.__anext__.side_effect = StopAsyncIteration

    adapter = AsyncEventStreamAdapter(mock_stream)

    with pytest.raises(StopAsyncIteration):
        await adapter.__anext__()


def test_make_api_call_patch_converse_with_messages(mock_tracer, mock_span):
    """Test that messages are properly processed when span is recording."""
    patcher = make_api_call_patch(mock_tracer)
    wrapped = Mock()
    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"
    kwargs = {
        "modelId": "test-model",
        "messages": [
            {"role": "user", "content": [{"text": "Hello"}]},
            {"role": "assistant", "content": [{"text": "Hi there!"}]},
        ],
    }
    args = ("Converse", kwargs)
    wrapped.return_value = {"response": True}

    result = patcher(wrapped, instance, args, {})
    assert result == {"response": True}
    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_make_api_call_async_patch_converse_with_messages(mock_tracer, mock_span):
    """Test async converse with messages processing."""
    patcher = make_api_call_async_patch(mock_tracer)
    wrapped = Mock()

    async def async_mock(*_args, **_kwargs):
        return {"async_response": True}

    wrapped.side_effect = async_mock

    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"
    kwargs = {
        "modelId": "test-model",
        "messages": [
            {"role": "user", "content": [{"text": "Hello"}]},
        ],
    }
    args = ("Converse", kwargs)

    result = await patcher(wrapped, instance, args, {})
    assert result == {"async_response": True}
    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.end.assert_called_once()


def test_sync_event_stream_adapter_iter():
    """Test SyncEventStreamAdapter __iter__ method."""
    mock_stream = MagicMock(spec=EventStream)
    mock_stream.__iter__.return_value = iter(["chunk1", "chunk2"])

    adapter = SyncEventStreamAdapter(mock_stream)

    # Test that __iter__ returns self (line 32)
    assert adapter.__iter__() is adapter

    # Test that it can be iterated
    chunks = list(adapter)
    assert chunks == ["chunk1", "chunk2"]


def test_async_event_stream_adapter_aiter():
    """Test AsyncEventStreamAdapter __aiter__ method."""
    mock_stream = MagicMock()

    adapter = AsyncEventStreamAdapter(mock_stream)

    # Test that __aiter__ returns self (line 45)
    assert adapter.__aiter__() is adapter


def test_make_api_call_patch_converse_stream_no_stream(mock_tracer, mock_span):
    """Test ConverseStream when response has no stream key."""
    patcher = make_api_call_patch(mock_tracer)
    wrapped = Mock()
    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"

    kwargs = {"modelId": "test-model"}
    args = ("ConverseStream", kwargs)
    # Response without stream key - should trigger else branch (lines 123-124)
    wrapped.return_value = {"response": "no_stream"}

    result = patcher(wrapped, instance, args, {})
    assert result == {"response": "no_stream"}
    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.end.assert_called_once()


def test_make_api_call_patch_converse_stream_error(mock_tracer, mock_span):
    """Test ConverseStream when exception occurs."""
    patcher = make_api_call_patch(mock_tracer)
    wrapped = Mock(side_effect=Exception("stream error"))
    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"

    kwargs = {"modelId": "test-model"}
    args = ("ConverseStream", kwargs)

    # Should trigger exception handling (lines 126-132)
    with pytest.raises(Exception, match="stream error"):
        patcher(wrapped, instance, args, {})

    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.set_status.assert_called()
    status_arg = mock_span.set_status.call_args[0][0]
    assert status_arg.status_code == StatusCode.ERROR
    mock_span.set_attribute.assert_called()
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_make_api_call_async_patch_converse_stream_no_stream(mock_tracer, mock_span):
    """Test async ConverseStream when response has no stream key."""
    patcher = make_api_call_async_patch(mock_tracer)
    wrapped = Mock()

    async def async_mock(*_args, **_kwargs):
        # Response without stream key - should trigger else branch (lines 204-205)
        return {"response": "no_stream_async"}

    wrapped.side_effect = async_mock

    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"
    kwargs = {"modelId": "test-model"}
    args = ("ConverseStream", kwargs)

    result = await patcher(wrapped, instance, args, {})
    assert result == {"response": "no_stream_async"}
    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_make_api_call_async_patch_converse_stream_error(mock_tracer, mock_span):
    """Test async ConverseStream when exception occurs."""
    patcher = make_api_call_async_patch(mock_tracer)
    wrapped = Mock()

    async def raise_error(*_args, **_kwargs):
        raise Exception("async stream error")

    wrapped.side_effect = raise_error

    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"
    kwargs = {"modelId": "test-model"}
    args = ("ConverseStream", kwargs)

    # Should trigger exception handling (lines 207-213)
    with pytest.raises(Exception, match="async stream error"):
        await patcher(wrapped, instance, args, {})

    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.set_status.assert_called()
    status_arg = mock_span.set_status.call_args[0][0]
    assert status_arg.status_code == StatusCode.ERROR
    mock_span.set_attribute.assert_called()
    mock_span.end.assert_called_once()
