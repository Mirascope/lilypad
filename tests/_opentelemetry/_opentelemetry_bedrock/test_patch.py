"""Tests for Bedrock OpenTelemetry patching."""

from unittest.mock import AsyncMock, Mock

import pytest
from opentelemetry.trace import StatusCode

from lilypad._opentelemetry._opentelemetry_bedrock import (
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
        class SpanContext:
            def __enter__(self):
                return mock_span

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        return SpanContext()

    tracer.start_as_current_span.side_effect = start_as_current_span
    return tracer


def test_bedrock_converse_success(mock_tracer, mock_span):
    wrapped = Mock()
    wrapped.return_value = {
        "output": {"message": {"content": [{"text": "Recommended: The Hobbit"}]}},
        "usage": {"inputTokens": 10, "outputTokens": 20},
        "stopReason": "stop",
    }

    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"
    args = ("Converse", {"modelId": "some_model_id", "messages": []})
    kwargs = {}

    wrapper = make_api_call_patch(mock_tracer)
    result = wrapper(wrapped, instance, args, kwargs)

    assert (
        result["output"]["message"]["content"][0]["text"] == "Recommended: The Hobbit"
    )
    wrapped.assert_called_once()
    mock_span.set_attributes.assert_called_once()
    mock_span.add_event.assert_called_once()


def test_bedrock_converse_other_operation(mock_tracer, mock_span):
    wrapped = Mock(return_value={"some": "response"})
    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"
    args = ("OtherOperation", {"modelId": "some_model_id", "messages": []})
    kwargs = {}

    wrapper = make_api_call_patch(mock_tracer)
    result = wrapper(wrapped, instance, args, kwargs)
    assert result == {"some": "response"}

    wrapped.assert_called_once()
    mock_span.set_attributes.assert_not_called()
    mock_span.add_event.assert_not_called()


def test_bedrock_converse_other_service(mock_tracer, mock_span):
    wrapped = Mock(return_value={"some": "response"})
    instance = Mock()
    instance.meta.service_model.service_name = "other-service"
    args = ("Converse", {"modelId": "some_model_id", "messages": []})
    kwargs = {}

    wrapper = make_api_call_patch(mock_tracer)
    result = wrapper(wrapped, instance, args, kwargs)
    assert result == {"some": "response"}

    wrapped.assert_called_once()
    mock_span.set_attributes.assert_not_called()
    mock_span.add_event.assert_not_called()


def test_bedrock_converse_error(mock_tracer, mock_span):
    error = Exception("Bedrock error")
    wrapped = Mock(side_effect=error)
    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"
    args = ("Converse", {"modelId": "some_model_id", "messages": []})
    kwargs = {}

    wrapper = make_api_call_patch(mock_tracer)
    with pytest.raises(Exception) as exc_info:
        wrapper(wrapped, instance, args, kwargs)

    assert exc_info.value is error
    mock_span.set_status.assert_called_once()
    called_status = mock_span.set_status.call_args[0][0]
    assert called_status.status_code == StatusCode.ERROR
    assert called_status.description == str(error)


@pytest.mark.asyncio
async def test_bedrock_converse_success_async(mock_tracer, mock_span):
    wrapped = AsyncMock()
    wrapped.return_value = {
        "output": {"message": {"content": [{"text": "Recommended: The Hobbit"}]}},
        "usage": {"inputTokens": 10, "outputTokens": 20},
        "stopReason": "stop",
    }

    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"
    args = ("Converse", {"modelId": "some_model_id", "messages": []})
    kwargs = {}

    wrapper = make_api_call_async_patch(mock_tracer)
    result = await wrapper(wrapped, instance, args, kwargs)

    assert (
        result["output"]["message"]["content"][0]["text"] == "Recommended: The Hobbit"
    )
    wrapped.assert_awaited_once()
    mock_span.set_attributes.assert_called_once()
    mock_span.add_event.assert_called_once()


@pytest.mark.asyncio
async def test_bedrock_converse_other_operation_async(mock_tracer, mock_span):
    wrapped = AsyncMock(return_value={"some": "response"})
    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"
    args = ("OtherOperation", {"modelId": "some_model_id", "messages": []})
    kwargs = {}

    wrapper = make_api_call_async_patch(mock_tracer)
    result = await wrapper(wrapped, instance, args, kwargs)
    assert result == {"some": "response"}

    wrapped.assert_awaited_once()
    mock_span.set_attributes.assert_not_called()
    mock_span.add_event.assert_not_called()


@pytest.mark.asyncio
async def test_bedrock_converse_other_service_async(mock_tracer, mock_span):
    wrapped = AsyncMock(return_value={"some": "response"})
    instance = Mock()
    instance.meta.service_model.service_name = "other-service"
    args = ("Converse", {"modelId": "some_model_id", "messages": []})
    kwargs = {}

    wrapper = make_api_call_async_patch(mock_tracer)
    result = await wrapper(wrapped, instance, args, kwargs)
    assert result == {"some": "response"}

    wrapped.assert_awaited_once()
    mock_span.set_attributes.assert_not_called()
    mock_span.add_event.assert_not_called()


@pytest.mark.asyncio
async def test_bedrock_converse_error_async(mock_tracer, mock_span):
    error = Exception("Async Bedrock error")
    wrapped = AsyncMock(side_effect=error)
    instance = Mock()
    instance.meta.service_model.service_name = "bedrock-runtime"
    args = ("Converse", {"modelId": "some_model_id", "messages": []})
    kwargs = {}

    wrapper = make_api_call_async_patch(mock_tracer)
    with pytest.raises(Exception) as exc_info:
        await wrapper(wrapped, instance, args, kwargs)

    assert exc_info.value is error
    mock_span.set_status.assert_called_once()
    called_status = mock_span.set_status.call_args[0][0]
    assert called_status.status_code == StatusCode.ERROR
    assert called_status.description == str(error)
