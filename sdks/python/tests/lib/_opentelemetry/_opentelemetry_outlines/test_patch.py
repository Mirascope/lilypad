"""Tests for model_generate, model_generate_stream, and model_generate_async decorators."""

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest
from opentelemetry.trace import Span, StatusCode

from lilypad.lib._opentelemetry._opentelemetry_outlines.patch import (
    model_generate,
    model_generate_async,
    model_generate_stream,
)


class FakeGenerationParameters:
    def __init__(self, stop_at=None, max_tokens=100, seed=42):
        self.stop_at = stop_at
        self.max_tokens = max_tokens
        self.seed = seed


class FakeSamplingParameters:
    def __init__(
        self,
        sampler="multinomial",
        num_samples=1,
        top_p=0.9,
        top_k=None,
        temperature=0.5,
    ):
        self.sampler = sampler
        self.num_samples = num_samples
        self.top_p = top_p
        self.top_k = top_k
        self.temperature = temperature


@pytest.fixture
def mock_span():
    span = MagicMock(spec=Span)
    span.is_recording.return_value = True
    return span


@pytest.fixture
def mock_tracer(mock_span):
    tracer = MagicMock()

    @contextmanager
    def start_current_span(*args, **kwargs):
        yield mock_span

    tracer.start_as_current_span.side_effect = start_current_span
    return tracer


class MockModel:
    model_name = "mock-model"

    def generate(self, prompts, generation_parameters, logits_processor, sampling_parameters):
        return "sync result"

    def stream(self, prompts, **kwargs):
        yield "partial"
        yield "final"

    async def generate_chat(self, prompts, gp, lp, sp, extra):
        return "async result"


def test_model_generate(mock_tracer, mock_span):
    decorated = model_generate(mock_tracer)

    # Use real parameters instead of Mock to avoid serialization errors
    gp = FakeGenerationParameters(stop_at="STOP", max_tokens=100, seed=42)
    lp = object()  # not used for json
    sp = FakeSamplingParameters()
    mock_model = MockModel()
    result = decorated(mock_model.generate, mock_model, ("prompt", gp, lp, sp), {})
    assert result == "sync result"
    mock_span.end.assert_called_once()


def test_model_generate_error(mock_tracer, mock_span):
    class ErrorMockModel(MockModel):
        def error_generate(self, prompts, gp, lp, sp):
            raise Exception("Test error")

    decorated_error = model_generate(mock_tracer)
    gp = FakeGenerationParameters(stop_at="STOP", max_tokens=100, seed=42)
    lp = object()
    sp = FakeSamplingParameters()

    mock_model = ErrorMockModel()

    with pytest.raises(Exception) as exc_info:
        decorated_error(mock_model.error_generate, mock_model, ("prompt", gp, lp, sp), {})
    assert str(exc_info.value) == "Test error"
    mock_span.set_status.assert_called_once()
    status_call = mock_span.set_status.call_args[0][0]
    assert status_call.status_code == StatusCode.ERROR
    assert status_call.description == "Test error"
    mock_span.end.assert_called_once()


def test_model_generate_stream(mock_tracer, mock_span):
    decorated = model_generate_stream(mock_tracer)

    # stream decorator fetches generation_parameters, sampling_parameters from kwargs if needed
    # but we do not specify them if not required. If needed, do `decorated(MockModel(), "prompt", generation_parameters=gp, sampling_parameters=sp)`
    mock_model = MockModel()
    chunks = list(decorated(mock_model.stream, mock_model, ("prompt",), {}))
    assert chunks == ["partial", "final"]
    mock_span.end.assert_called_once()


def test_model_generate_stream_error(mock_tracer, mock_span):
    class ErrorMockModel(MockModel):
        def error_stream(self, prompts, **kwargs):
            yield "partial"
            raise Exception("Stream error")

    decorated_error = model_generate_stream(mock_tracer)
    gp = FakeGenerationParameters(stop_at="STOP", max_tokens=100, seed=42)
    mock_model = ErrorMockModel()
    with pytest.raises(Exception) as exc_info:
        list(
            decorated_error(
                mock_model.error_stream,
                mock_model,
                ("prompt",),
                {"generation_parameters": gp},
            )
        )
    assert str(exc_info.value) == "Stream error"
    mock_span.set_status.assert_called_once()
    status_call = mock_span.set_status.call_args[0][0]
    assert status_call.status_code == StatusCode.ERROR
    assert status_call.description == "Stream error"
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_model_generate_async(mock_tracer, mock_span):
    decorated = model_generate_async(mock_tracer)

    gp = FakeGenerationParameters(stop_at="STOP")
    lp = object()
    sp = FakeSamplingParameters()

    mock_model = MockModel()
    result = await decorated(mock_model.generate_chat, mock_model, ("prompt", gp, lp, sp, None), {})
    assert result == "async result"
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_model_generate_async_error(mock_tracer, mock_span):
    class ErrorMockModel(MockModel):
        async def error_async(self, prompts, gp, lp, sp, extra):
            raise Exception("Async error")

    decorated_error = model_generate_async(mock_tracer)
    gp = FakeGenerationParameters(stop_at="STOP")
    lp = object()
    sp = FakeSamplingParameters()
    mock_model = ErrorMockModel()
    with pytest.raises(Exception) as exc_info:
        await decorated_error(mock_model.error_async, mock_model, ("prompt", gp, lp, sp, None), {})
    assert str(exc_info.value) == "Async error"
    mock_span.set_status.assert_called_once()
    status_call = mock_span.set_status.call_args[0][0]
    assert status_call.status_code == StatusCode.ERROR
    assert status_call.description == "Async error"
    mock_span.end.assert_called_once()
