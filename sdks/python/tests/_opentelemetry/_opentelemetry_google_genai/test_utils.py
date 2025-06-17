import json
from enum import Enum
from unittest.mock import Mock, patch

import pytest
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from lilypad._opentelemetry._opentelemetry_google_genai.utils import (
    set_stream,
    set_stream_async,
    set_content_event,
    set_response_attributes,
    get_llm_request_attributes,
    get_tool_calls,
    get_candidate_event,
)


class FinishReason(Enum):
    STOP = "STOP"
    COMPLETED = "COMPLETED"
    TIMEOUT = "TIMEOUT"


class DummyCandidate:
    def __init__(self, index, finish_reason: FinishReason, content=None):
        self.index = index
        self.finish_reason = finish_reason
        self.content = content


class DummyChunk:
    def __init__(self, candidates):
        self.candidates = candidates


@pytest.fixture
def instance():
    obj = Mock()
    return obj


def test_get_llm_request_attributes(instance):
    kwargs = {
        "config": {
            "temperature": 0.8,
            "top_p": 0.95,
            "top_k": 50,
            "max_output_tokens": 200,
        },
        "stream": True,
        "model": "google-genai-model",
    }
    attrs = get_llm_request_attributes(kwargs, instance)
    assert attrs[gen_ai_attributes.GEN_AI_OPERATION_NAME] == "generate_content"
    assert attrs[gen_ai_attributes.GEN_AI_SYSTEM] == "google_genai"
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_MODEL] == "google-genai-model"
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE] == 0.8
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_TOP_P] == 0.95
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_TOP_K] == 50
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS] == 200
    assert attrs["google_genai.stream"] is True


def test_set_content_event():
    span = Mock()
    content = {"role": "user", "parts": ["Test message"]}
    set_content_event(span, content)
    expected_attributes = {
        "gen_ai.system": "google_genai",
        "content": json.dumps(["Test message"]),
    }
    span.add_event.assert_called_once_with("gen_ai.user.message", attributes=expected_attributes)


def test_set_response_attributes(instance):
    span = Mock()
    candidate1 = DummyCandidate(0, FinishReason.COMPLETED, content=None)
    candidate2 = DummyCandidate(1, FinishReason.COMPLETED, content=None)
    response = Mock(model_version="google-genai-model")
    response.candidates = [candidate1, candidate2]
    set_response_attributes(span, response)
    assert span.add_event.call_count == 2
    span.set_attributes.assert_called_once()
    attrs = span.set_attributes.call_args[0][0]
    assert attrs[gen_ai_attributes.GEN_AI_RESPONSE_MODEL] == "google-genai-model"
    assert gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS in attrs
    assert attrs[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] == [
        "COMPLETED",
        "COMPLETED",
    ]


def test_set_stream():
    span = Mock()
    candidate = DummyCandidate(0, FinishReason.COMPLETED, content=None)
    chunk1 = DummyChunk([candidate])
    chunk2 = DummyChunk([candidate])
    stream = [chunk1, chunk2]
    instance = Mock()
    instance._model_name = "google-genai-model"
    set_stream(span, stream, instance)
    span.set_attributes.assert_called_once()
    assert span.add_event.call_count >= 2


@pytest.mark.asyncio
async def test_set_stream_async():
    span = Mock()
    candidate = DummyCandidate(0, FinishReason.COMPLETED, content=None)
    chunk = DummyChunk([candidate])

    async def async_stream():
        yield chunk
        yield chunk

    instance = Mock()
    instance._model_name = "google-genai-model"
    await set_stream_async(span, async_stream(), instance)
    span.set_attributes.assert_called()
    assert span.add_event.call_count >= 2


def test_get_tool_calls_with_function_call():
    """Test get_tool_calls with parts containing function calls (lines 41-54)."""
    # Mock parts with function calls
    mock_part = Mock()
    mock_function_call = Mock()
    mock_function_call.name = "test_function"
    mock_function_call.args = {"arg1": "value1", "arg2": "value2"}
    mock_part.function_call = mock_function_call

    parts = [mock_part]
    result = get_tool_calls(parts)

    assert len(result) == 1
    assert result[0]["type"] == "function"
    assert result[0]["function"]["name"] == "test_function"
    assert result[0]["function"]["arguments"] == {"arg1": "value1", "arg2": "value2"}


def test_get_tool_calls_without_function_call():
    """Test get_tool_calls with parts without function calls."""
    mock_part = Mock()
    mock_part.function_call = None

    parts = [mock_part]
    result = get_tool_calls(parts)

    assert result == []


def test_set_content_event_with_binary_data():
    """Test set_content_event with binary data (lines 66-71)."""
    span = Mock()
    content = {"role": "user", "parts": [{"mime_type": "image/png", "data": b"test_binary_data"}]}

    set_content_event(span, content)
    span.add_event.assert_called_once()


def test_set_content_event_with_webp_image():
    """Test set_content_event with WebP image (lines 72-81)."""
    import PIL.Image
    from io import BytesIO

    span = Mock()

    # Create a mock WebP image
    image = PIL.Image.new("RGB", (10, 10), color="red")
    buffered = BytesIO()
    image.save(buffered, format="WEBP")

    # Mock WebPImageFile
    mock_webp = Mock()
    mock_webp.save = Mock()

    content = {"role": "user", "parts": [mock_webp]}

    # Mock isinstance to return True for WebPImageFile
    PIL_WebPImagePlugin = pytest.importorskip("PIL.WebPImagePlugin")
    with patch("lilypad._opentelemetry._opentelemetry_google_genai.utils.isinstance") as mock_isinstance:
        mock_isinstance.side_effect = lambda obj, cls: cls == PIL_WebPImagePlugin.WebPImageFile
        set_content_event(span, content)
        span.add_event.assert_called_once()


def test_set_content_event_with_tool_calls():
    """Test set_content_event with model role and tool calls (lines 85-86)."""
    span = Mock()

    # Mock parts with function calls
    mock_part = Mock()
    mock_function_call = Mock()
    mock_function_call.name = "test_function"
    mock_function_call.args = {"arg1": "value1"}
    mock_part.function_call = mock_function_call

    content = {"role": "model", "parts": [mock_part]}

    set_content_event(span, content)
    span.add_event.assert_called_once()


def test_get_candidate_event_with_content():
    """Test get_candidate_event with candidate content (lines 97-106)."""
    # Mock candidate with content
    mock_candidate = Mock()
    mock_content = Mock()
    mock_content.role = "assistant"

    # Mock parts with text
    mock_part = Mock()
    mock_part.text = "response text"
    mock_content.parts = [mock_part]

    # Mock tool calls
    mock_function_call = Mock()
    mock_function_call.name = "test_function"
    mock_function_call.args = {}
    mock_part.function_call = mock_function_call

    mock_candidate.content = mock_content
    mock_candidate.index = 0
    mock_candidate.finish_reason = Mock()
    mock_candidate.finish_reason.value = "STOP"

    result = get_candidate_event(mock_candidate)

    assert "message" in result
    assert result["index"] == 0
    assert result["finish_reason"] == "STOP"


def test_set_stream_with_id_and_usage():
    """Test set_stream with chunks containing id and usage_metadata (lines 152, 154-155, 159, 161)."""
    span = Mock()

    # Mock chunk with id and usage
    mock_chunk = Mock()
    mock_chunk.id = "test_chunk_id"

    mock_usage = Mock()
    mock_usage.prompt_token_count = 10
    mock_usage.candidates_token_count = 20
    mock_chunk.usage_metadata = mock_usage

    mock_chunk.candidates = []  # No candidates for simplicity

    def stream_generator():
        yield mock_chunk

    instance = Mock()
    instance._model_name = "test_model"

    set_stream(span, stream_generator(), instance)

    # Verify span.set_attributes was called
    span.set_attributes.assert_called()

    # Check that the attributes contain the expected values
    call_args = span.set_attributes.call_args[0][0]
    assert call_args[gen_ai_attributes.GEN_AI_RESPONSE_ID] == "test_chunk_id"
    assert call_args[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] == 10
    assert call_args[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] == 20


@pytest.mark.asyncio
async def test_set_stream_async_with_id_and_usage():
    """Test set_stream_async with chunks containing id and usage_metadata (lines 183, 185-186, 190, 192)."""
    span = Mock()

    # Mock chunk with id and usage
    mock_chunk = Mock()
    mock_chunk.id = "test_chunk_id_async"

    mock_usage = Mock()
    mock_usage.prompt_token_count = 15
    mock_usage.candidates_token_count = 25
    mock_chunk.usage_metadata = mock_usage

    mock_chunk.candidates = []  # No candidates for simplicity

    async def async_stream():
        yield mock_chunk

    instance = Mock()
    instance.model_version = "test_model_async"

    await set_stream_async(span, async_stream(), instance)

    # Verify span.set_attributes was called
    span.set_attributes.assert_called()

    # Check that the attributes contain the expected values
    call_args = span.set_attributes.call_args[0][0]
    assert call_args[gen_ai_attributes.GEN_AI_RESPONSE_ID] == "test_chunk_id_async"
    assert call_args[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] == 15
    assert call_args[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] == 25
