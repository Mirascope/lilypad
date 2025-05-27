from unittest.mock import Mock, MagicMock

import pytest
from opentelemetry.trace import StatusCode
from botocore.eventstream import EventStream

from lilypad.lib._opentelemetry._opentelemetry_bedrock.patch import (
    make_api_call_patch,
    make_api_call_async_patch,
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
