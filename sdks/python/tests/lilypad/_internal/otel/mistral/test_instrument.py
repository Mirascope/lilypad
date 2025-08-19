import os
from unittest.mock import Mock, patch
from importlib.metadata import PackageNotFoundError

import pytest
from wrapt import FunctionWrapper
from dotenv import load_dotenv
from mistralai import Mistral, SDKError
from mistralai.models import (
    ChatCompletionResponse,
)
from inline_snapshot import snapshot
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from lilypad._internal.otel.mistral.instrument import instrument_mistral

from ..test_utils import extract_span_data


@pytest.fixture
def mistral_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("MISTRAL_API_KEY", "test-api-key")
    return api_key


@pytest.fixture
def client(mistral_api_key: str) -> Mistral:
    client = Mistral(api_key=mistral_api_key)
    instrument_mistral(client)
    return client


@pytest.fixture
def async_client(mistral_api_key: str) -> Mistral:
    client = Mistral(api_key=mistral_api_key)
    instrument_mistral(client)
    return client


@pytest.mark.vcr()
def test_sync_completion_simple(
    client: Mistral, span_exporter: InMemorySpanExporter
) -> None:
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": "Hello, say 'Hi' back to me"}],
        max_tokens=50,
    )

    assert isinstance(response, ChatCompletionResponse)
    assert response.choices
    assert response.choices[0].message.content

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat mistral-small-latest",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.system": "mistral",
                "gen_ai.request.model": "mistral-small-latest",
                "gen_ai.request.max_tokens": 50,
                "gen_ai.response.model": "mistral-small-latest",
                "gen_ai.response.finish_reasons": ("stop",),
                "gen_ai.response.id": "91cd277babc241cd911078921779af63",
                "gen_ai.usage.input_tokens": 12,
                "gen_ai.usage.output_tokens": 14,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "mistral",
                        "content": "Hello, say 'Hi' back to me",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "mistral",
                        "message": '{"role": "assistant", "content": "Hi there! \\ud83d\\ude0a How can I help you today?"}',
                        "index": 0,
                        "finish_reason": "stop",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_completion_with_system_message(
    client: Mistral, span_exporter: InMemorySpanExporter
) -> None:
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Count from 1 to 3"},
    ]

    response = client.chat.complete(
        model="mistral-small-latest",
        messages=messages,
        max_tokens=50,
        temperature=0.7,
    )

    assert isinstance(response, ChatCompletionResponse)
    assert response.choices

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat mistral-small-latest",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.system": "mistral",
                "gen_ai.request.model": "mistral-small-latest",
                "gen_ai.request.temperature": 0.7,
                "gen_ai.request.max_tokens": 50,
                "gen_ai.response.model": "mistral-small-latest",
                "gen_ai.response.finish_reasons": ("stop",),
                "gen_ai.response.id": "6c1d08c94bfc4562bbc379704b998e68",
                "gen_ai.usage.input_tokens": 17,
                "gen_ai.usage.output_tokens": 12,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.system.message",
                    "attributes": {
                        "gen_ai.system": "mistral",
                        "content": "You are a helpful assistant",
                    },
                },
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "mistral",
                        "content": "Count from 1 to 3",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "mistral",
                        "message": '{"role": "assistant", "content": "Sure, here you go:\\n\\n1\\n2\\n3"}',
                        "index": 0,
                        "finish_reason": "stop",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_completion_with_top_p(
    client: Mistral, span_exporter: InMemorySpanExporter
) -> None:
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": "Write the number 42"}],
        max_tokens=20,
        top_p=0.9,
    )

    assert isinstance(response, ChatCompletionResponse)
    assert response.choices

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    span_data = extract_span_data(spans[0])
    assert span_data["attributes"]["gen_ai.request.top_p"] == 0.9
    assert span_data["attributes"]["gen_ai.request.max_tokens"] == 20


@pytest.mark.vcr()
def test_sync_completion_with_multiple_messages(
    client: Mistral, span_exporter: InMemorySpanExporter
) -> None:
    messages = [
        {"role": "user", "content": "My name is Alice"},
        {"role": "assistant", "content": "Nice to meet you, Alice!"},
        {"role": "user", "content": "What's my name?"},
    ]

    response = client.chat.complete(
        model="mistral-small-latest",
        messages=messages,
        max_tokens=50,
    )

    assert isinstance(response, ChatCompletionResponse)
    assert "Alice" in response.choices[0].message.content

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat mistral-small-latest",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.system": "mistral",
                "gen_ai.request.model": "mistral-small-latest",
                "gen_ai.request.max_tokens": 50,
                "gen_ai.response.model": "mistral-small-latest",
                "gen_ai.response.finish_reasons": ("stop",),
                "gen_ai.response.id": "1d1aa7fcefeb44ebba20b98c3816062c",
                "gen_ai.usage.input_tokens": 22,
                "gen_ai.usage.output_tokens": 33,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "mistral",
                        "content": "My name is Alice",
                    },
                },
                {
                    "name": "gen_ai.assistant.message",
                    "attributes": {
                        "gen_ai.system": "mistral",
                        "content": "Nice to meet you, Alice!",
                    },
                },
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "mistral",
                        "content": "What's my name?",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "mistral",
                        "message": '{"role": "assistant", "content": "Your name is **Alice**\\u2014you just told me! \\ud83d\\ude0a\\n\\n(Unless you were testing me, in which case: *gotcha!*)"}',
                        "index": 0,
                        "finish_reason": "stop",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_async_completion_simple(
    async_client: Mistral, span_exporter: InMemorySpanExporter
) -> None:
    response = await async_client.chat.complete_async(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": "Hello, say 'Hi' back to me"}],
        max_tokens=50,
    )

    assert isinstance(response, ChatCompletionResponse)
    assert response.choices
    assert response.choices[0].message.content

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat mistral-small-latest",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.system": "mistral",
                "gen_ai.request.model": "mistral-small-latest",
                "gen_ai.request.max_tokens": 50,
                "gen_ai.response.model": "mistral-small-latest",
                "gen_ai.response.finish_reasons": ("stop",),
                "gen_ai.response.id": "f551761f708a47c69c0527b5de22a2d1",
                "gen_ai.usage.input_tokens": 12,
                "gen_ai.usage.output_tokens": 14,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "mistral",
                        "content": "Hello, say 'Hi' back to me",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "mistral",
                        "message": '{"role": "assistant", "content": "Hi there! \\ud83d\\ude0a How can I help you today?"}',
                        "index": 0,
                        "finish_reason": "stop",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_async_completion_with_temperature(
    async_client: Mistral, span_exporter: InMemorySpanExporter
) -> None:
    response = await async_client.chat.complete_async(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": "Write the word 'test'"}],
        max_tokens=10,
        temperature=0.0,
    )

    assert isinstance(response, ChatCompletionResponse)
    assert response.choices

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    span_data = extract_span_data(spans[0])
    assert span_data["attributes"]["gen_ai.request.temperature"] == 0.0
    assert span_data["attributes"]["gen_ai.request.max_tokens"] == 10


def test_instrumentation_idempotency(
    mistral_api_key: str, span_exporter: InMemorySpanExporter
) -> None:
    client = Mistral(api_key=mistral_api_key)

    instrument_mistral(client)
    instrument_mistral(client)

    assert hasattr(client, "_lilypad_instrumented")
    assert isinstance(client.chat.complete, FunctionWrapper)


def test_multiple_client_instances(
    mistral_api_key: str, span_exporter: InMemorySpanExporter
) -> None:
    client1 = Mistral(api_key=mistral_api_key)
    client2 = Mistral(api_key=mistral_api_key)

    instrument_mistral(client1)
    instrument_mistral(client2)

    assert hasattr(client1, "_lilypad_instrumented")
    assert hasattr(client2, "_lilypad_instrumented")
    assert isinstance(client1.chat.complete, FunctionWrapper)
    assert isinstance(client2.chat.complete, FunctionWrapper)


@patch("lilypad._internal.otel.mistral.instrument.version")
def test_package_not_found(
    mock_version: Mock, mistral_api_key: str, span_exporter: InMemorySpanExporter
) -> None:
    mock_version.side_effect = PackageNotFoundError("lilypad-sdk")

    client = Mistral(api_key=mistral_api_key)
    instrument_mistral(client)

    assert hasattr(client, "_lilypad_instrumented")
    assert isinstance(client.chat.complete, FunctionWrapper)


def test_wrapping_failure_logging(
    mistral_api_key: str,
    span_exporter: InMemorySpanExporter,
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = Mistral(api_key=mistral_api_key)

    class ReadOnlyChat:
        @property
        def complete(self):
            return Mock()

        @property
        def complete_async(self):
            return Mock()

    client.chat = ReadOnlyChat()  # type: ignore[assignment]

    with caplog.at_level("WARNING"):
        instrument_mistral(client)

    assert "Failed to wrap Mistral.chat.complete" in caplog.text


@pytest.mark.vcr()
def test_sync_error_handling(
    client: Mistral, span_exporter: InMemorySpanExporter
) -> None:
    with pytest.raises(SDKError):
        client.chat.complete(
            model="invalid-model-xyz",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=50,
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    span_data = extract_span_data(spans[0])
    assert span_data["status"]["status_code"] == "ERROR"
    assert "error.type" in span_data["attributes"]


@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_async_error_handling(
    async_client: Mistral, span_exporter: InMemorySpanExporter
) -> None:
    with pytest.raises(SDKError):
        await async_client.chat.complete_async(
            model="invalid-model-xyz",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=50,
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    span_data = extract_span_data(spans[0])
    assert span_data["status"]["status_code"] == "ERROR"
    assert "error.type" in span_data["attributes"]
