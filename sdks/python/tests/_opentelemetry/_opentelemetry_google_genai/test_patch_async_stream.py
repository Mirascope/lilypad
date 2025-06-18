"""Test for async streaming with stream=True parameter to cover lines 110-137."""

import pytest
from contextlib import contextmanager
from unittest.mock import Mock, AsyncMock
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from lilypad._opentelemetry._opentelemetry_google_genai.patch import (
    generate_content_async,
)


@pytest.fixture
def mock_span():
    span = Mock()
    span.is_recording.return_value = True
    return span


@pytest.fixture
def mock_tracer(mock_span):
    tracer = Mock()

    @contextmanager
    def start_span(*args, **kwargs):
        yield mock_span

    tracer.start_as_current_span.side_effect = start_span
    return tracer


@pytest.mark.asyncio
async def test_generate_content_async_with_stream_true_parameter(mock_tracer, mock_span):
    """Test generate_content_async with stream=True parameter (covers lines 110-137)."""

    class MockFinishReason:
        def __init__(self, value):
            self.value = value

    class DummyCandidate:
        def __init__(self, index, finish_reason_value):
            self.index = index
            self.finish_reason = MockFinishReason(finish_reason_value) if finish_reason_value else None

    class DummyChunk:
        def __init__(self, candidates):
            self.candidates = candidates

    # Create candidates with different finish reasons
    candidate1 = DummyCandidate(0, "STOP")
    candidate2 = DummyCandidate(1, "MAX_TOKENS")
    candidate_no_finish = DummyCandidate(2, None)  # No finish reason

    async def async_stream():
        yield DummyChunk([candidate1])
        yield DummyChunk([candidate2])
        yield DummyChunk([candidate_no_finish])
        yield DummyChunk([])  # Chunk with no candidates

    wrapped = AsyncMock()
    wrapped.return_value = async_stream()
    instance = Mock(_model_name="google-genai-model")
    kwargs = {
        "contents": [{"role": "user", "parts": ["Test streaming"]}],
        "stream": True,  # This is in kwargs but decorator also needs stream=True
    }

    # Create decorator with stream=True to trigger lines 110-137
    decorator = generate_content_async(mock_tracer, stream=True)
    result = await decorator(wrapped, instance, (), kwargs)

    # Process the stream - this will execute the wrapper code
    chunks = []
    async for chunk in result:
        chunks.append(chunk)

    assert len(chunks) == 4

    # Verify candidate events were added
    assert mock_span.add_event.call_count >= 3  # At least 3 candidate events

    # Verify the candidate events have correct attributes
    candidate_event_calls = [call for call in mock_span.add_event.call_args_list if call[0][0] == "gen_ai.candidate"]
    assert len(candidate_event_calls) == 3

    # Check first candidate event
    first_event_attrs = candidate_event_calls[0][1]["attributes"]
    assert first_event_attrs["candidate_index"] == 0
    assert first_event_attrs["finish_reason"] == ("STOP",)

    # Check second candidate event
    second_event_attrs = candidate_event_calls[1][1]["attributes"]
    assert second_event_attrs["candidate_index"] == 1
    assert second_event_attrs["finish_reason"] == ("MAX_TOKENS",)

    # Check third candidate event (no finish reason)
    third_event_attrs = candidate_event_calls[2][1]["attributes"]
    assert third_event_attrs["candidate_index"] == 2
    assert third_event_attrs["finish_reason"] == ("none",)

    # Verify finish reasons were set in span attributes
    mock_span.set_attributes.assert_called()
    set_attrs_calls = mock_span.set_attributes.call_args_list
    # Find the call that sets finish reasons
    for call in set_attrs_calls:
        attrs = call[0][0]
        if gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS in attrs:
            # Should set the first finish reason
            assert attrs[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] == ("STOP",)
            break
    else:
        pytest.fail("GEN_AI_RESPONSE_FINISH_REASONS not set")

    # Verify span.end was called
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_generate_content_async_stream_with_exception(mock_tracer, mock_span):
    """Test async streaming exception handling in the wrapper."""

    class DummyCandidate:
        def __init__(self, index):
            self.index = index
            self.finish_reason = None

    class DummyChunk:
        def __init__(self, candidates):
            self.candidates = candidates

    async def async_stream():
        yield DummyChunk([DummyCandidate(0)])
        raise RuntimeError("Stream error")

    wrapped = AsyncMock()
    wrapped.return_value = async_stream()
    instance = Mock(_model_name="google-genai-model")
    kwargs = {
        "contents": [{"role": "user", "parts": ["Test streaming error"]}],
        "stream": True,
    }

    # Create decorator with stream=True
    decorator = generate_content_async(mock_tracer, stream=True)
    result = await decorator(wrapped, instance, (), kwargs)

    # Process the stream and expect exception
    chunks = []
    with pytest.raises(RuntimeError, match="Stream error"):
        async for chunk in result:
            chunks.append(chunk)

    assert len(chunks) == 1  # Got one chunk before error

    # Verify span.end was still called (in finally block)
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_generate_content_async_stream_empty_finish_reasons(mock_tracer, mock_span):
    """Test async streaming when no finish reasons are collected."""

    async def async_stream():
        # Yield chunks without candidates
        yield "chunk1"
        yield "chunk2"

    wrapped = AsyncMock()
    wrapped.return_value = async_stream()
    instance = Mock(_model_name="google-genai-model")
    kwargs = {
        "contents": [{"role": "user", "parts": ["Test no candidates"]}],
        "stream": True,
    }

    # Create decorator with stream=True
    decorator = generate_content_async(mock_tracer, stream=True)
    result = await decorator(wrapped, instance, (), kwargs)

    # Process the stream
    chunks = []
    async for chunk in result:
        chunks.append(chunk)

    assert len(chunks) == 2

    # Verify no finish reasons were set (line 126-127 not executed)
    set_attrs_calls = mock_span.set_attributes.call_args_list
    for call in set_attrs_calls:
        attrs = call[0][0] if call[0] else {}
        assert gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS not in attrs

    # Verify span.end was called
    mock_span.end.assert_called_once()
