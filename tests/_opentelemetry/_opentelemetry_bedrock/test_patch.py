"""Tests for Bedrock OpenTelemetry patching."""

from unittest.mock import MagicMock, Mock

import pytest
from botocore.eventstream import EventStream
from opentelemetry.trace import StatusCode

from lilypad._opentelemetry._opentelemetry_bedrock.patch import (
    make_api_call_async_patch,
    make_api_call_patch,
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
        return Mock(__enter__=lambda s: mock_span, __exit__=lambda s, e, v, tb: None)

    tracer.start_as_current_span.side_effect = start_as_current_span
    return tracer


def test_make_api_call_patch_converse_success(mock_tracer, mock_span):
    patcher = make_api_call_patch(mock_tracer)
    wrapped = Mock()
    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"

    kwargs = {"modelId": "test-model"}
    args = ("Converse", kwargs)
    wrapped.return_value = {"result": "ok"}
    result = patcher(wrapped, instance, args, {})
    assert result == {"result": "ok"}
    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.set_status.assert_not_called()
    mock_span.end.assert_called_once()


def test_make_api_call_patch_converse_stream_success(mock_tracer, mock_span):
    patcher = make_api_call_patch(mock_tracer)
    wrapped = Mock()
    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"

    # Make the fake_stream truly iterable
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
    chunks = list(stream_wrapper)  # Force iteration
    assert chunks == ["chunk1", "chunk2"]

    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.end.assert_not_called()


def test_make_api_call_patch_ignored_service(mock_tracer, mock_span):
    patcher = make_api_call_patch(mock_tracer)
    wrapped = Mock()
    instance = Mock()
    instance.meta.service_model.service_name = "other-service"
    args = ("Converse", {"modelId": "m"})
    patcher(wrapped, instance, args, {})
    mock_tracer.start_as_current_span.assert_not_called()


def test_make_api_call_patch_converse_error(mock_tracer, mock_span):
    patcher = make_api_call_patch(mock_tracer)
    wrapped = Mock(side_effect=Exception("test error"))
    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"
    kwargs = {"modelId": "test-model"}
    args = ("Converse", kwargs)
    with pytest.raises(Exception) as exc_info:
        patcher(wrapped, instance, args, {})
    assert "test error" in str(exc_info.value)
    mock_span.set_status.assert_called()
    called_status = mock_span.set_status.call_args[0][0]
    assert called_status.status_code == StatusCode.ERROR
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_make_api_call_async_patch_converse_success(mock_tracer, mock_span):
    patcher = make_api_call_async_patch(mock_tracer)
    wrapped = Mock()
    wrapped.__aiter__ = None

    async def async_mock(*_args, **_kwargs):
        return {"non_stream": True}

    wrapped.side_effect = async_mock
    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"
    kwargs = {"modelId": "test-model"}
    args = ("Converse", kwargs)
    resp = await patcher(wrapped, instance, args, {})
    assert resp == {"non_stream": True}
    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_make_api_call_async_patch_converse_stream_success(
    mock_tracer, mock_span
):
    patcher = make_api_call_async_patch(mock_tracer)
    wrapped = Mock()
    wrapped.__aiter__ = None

    async def async_mock(*_args, **_kwargs):
        fake_stream = MagicMock(spec=EventStream)
        # Make the fake async stream produce a few chunks
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
    mock_span.end.assert_not_called()


@pytest.mark.asyncio
async def test_make_api_call_async_patch_converse_error(mock_tracer, mock_span):
    patcher = make_api_call_async_patch(mock_tracer)
    wrapped = Mock()
    wrapped.__aiter__ = None

    async def raise_error(*_args, **_kwargs):
        raise Exception("async error")

    wrapped.side_effect = raise_error
    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"
    kwargs = {"modelId": "test-model"}
    args = ("Converse", kwargs)
    with pytest.raises(Exception) as exc_info:
        await patcher(wrapped, instance, args, {})
    assert "async error" in str(exc_info.value)
    mock_span.set_status.assert_called()
    called_status = mock_span.set_status.call_args[0][0]
    assert called_status.status_code == StatusCode.ERROR
    mock_span.end.assert_called_once()
