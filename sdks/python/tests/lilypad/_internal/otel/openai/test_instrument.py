"""Tests for OpenAI instrumentation."""

import os
import inspect
from typing import Any, Generator

import pytest
from wrapt import FunctionWrapper
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI, NotFoundError
from pydantic import BaseModel
from opentelemetry import trace
from inline_snapshot import snapshot
from opentelemetry.trace import ProxyTracerProvider
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from lilypad._internal.otel.openai.instrument import instrument_openai


def extract_span_data(span: ReadableSpan) -> dict[str, Any]:
    """Extract serializable data from a span for snapshot testing."""
    return {
        "name": span.name,
        "attributes": dict(span.attributes) if span.attributes else {},
        "status": {
            "status_code": span.status.status_code.name,
            "description": span.status.description,
        },
        "events": [
            {
                "name": event.name,
                "attributes": dict(event.attributes) if event.attributes else {},
            }
            for event in span.events
        ],
    }


@pytest.fixture
def api_key() -> str:
    """Get API key from environment or return dummy key."""
    load_dotenv()
    return os.getenv("OPENAI_API_KEY", "test-api-key")


@pytest.fixture
def span_exporter() -> Generator[InMemorySpanExporter, None, None]:
    """Set up InMemorySpanExporter for testing span content."""
    current_provider = trace.get_tracer_provider()
    if isinstance(current_provider, ProxyTracerProvider):
        provider = TracerProvider()
        trace.set_tracer_provider(provider)
    else:
        provider = current_provider
    exporter = InMemorySpanExporter()
    processor = SimpleSpanProcessor(exporter)
    provider.add_span_processor(processor)  # type: ignore[attr-defined]

    exporter.clear()
    yield exporter
    exporter.clear()


@pytest.fixture
def client(api_key: str) -> OpenAI:
    """Create an instrumented OpenAI client."""
    client = OpenAI(api_key=api_key)
    instrument_openai(client)
    return client


@pytest.fixture
def async_client(api_key: str) -> AsyncOpenAI:
    """Create an instrumented AsyncOpenAI client."""
    client = AsyncOpenAI(api_key=api_key)
    instrument_openai(client)
    return client


@pytest.mark.vcr()
def test_sync_chat_completion_simple(
    client: OpenAI, span_exporter: InMemorySpanExporter
):
    """Test basic chat completion with span verification."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello, say 'Hi' back to me"}],
    )

    assert response.id
    assert response.model
    assert response.choices
    assert len(response.choices) > 0
    assert response.choices[0].message.content

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gpt-4o-mini",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4o-mini",
                "server.address": "api.openai.com",
                "gen_ai.system": "openai",
                "gen_ai.response.model": "gpt-4o-mini-2024-07-18",
                "gen_ai.response.finish_reasons": ("stop",),
                "gen_ai.response.id": "chatcmpl-C2IjBmSRfYZ7cNPkwEnAk8wYnwrH8",
                "gen_ai.openai.request.service_tier": "default",
                "gen_ai.usage.input_tokens": 16,
                "gen_ai.usage.output_tokens": 9,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": "Hello, say 'Hi' back to me",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "message": '{"role":"assistant","content":"Hi! How can I assist you today?"}',
                        "index": 0,
                        "finish_reason": "stop",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_async_chat_completion_simple(
    async_client: AsyncOpenAI, span_exporter: InMemorySpanExporter
):
    """Test async chat completion with span verification."""
    response = await async_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello, say 'Hi' back to me"}],
    )

    assert response.id
    assert response.model
    assert response.choices
    assert len(response.choices) > 0
    assert response.choices[0].message.content

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gpt-4o-mini",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4o-mini",
                "server.address": "api.openai.com",
                "gen_ai.system": "openai",
                "gen_ai.response.model": "gpt-4o-mini-2024-07-18",
                "gen_ai.response.finish_reasons": ("stop",),
                "gen_ai.response.id": "chatcmpl-C2IjRxvoLho0bftsXItlOIcnRAW72",
                "gen_ai.openai.request.service_tier": "default",
                "gen_ai.usage.input_tokens": 16,
                "gen_ai.usage.output_tokens": 9,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": "Hello, say 'Hi' back to me",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "message": '{"role":"assistant","content":"Hi! How can I assist you today?"}',
                        "index": 0,
                        "finish_reason": "stop",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_chat_completion_with_system(
    client: OpenAI, span_exporter: InMemorySpanExporter
):
    """Test chat completion with system message and span verification."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant who speaks like a pirate.",
            },
            {"role": "user", "content": "What is the capital of France?"},
        ],
        temperature=0.7,
        max_tokens=100,
    )

    assert response.id
    assert response.choices
    assert response.choices[0].message.content
    assert (
        response.usage
        and response.usage.total_tokens <= 100 + response.usage.prompt_tokens
    )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gpt-4o-mini",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4o-mini",
                "gen_ai.request.temperature": 0.7,
                "gen_ai.request.max_tokens": 100,
                "server.address": "api.openai.com",
                "gen_ai.system": "openai",
                "gen_ai.response.model": "gpt-4o-mini-2024-07-18",
                "gen_ai.response.finish_reasons": ("stop",),
                "gen_ai.response.id": "chatcmpl-C2IjO5uwSx3aCf3XfzbiWRW8ZpZIM",
                "gen_ai.openai.request.service_tier": "default",
                "gen_ai.usage.input_tokens": 29,
                "gen_ai.usage.output_tokens": 29,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.system.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": "You are a helpful assistant who speaks like a pirate.",
                    },
                },
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": "What is the capital of France?",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "message": '{"role":"assistant","content":"Arrr, matey! The capital of France be Paris, the City of Light! A fine place fer treasure and adventure, it be!"}',
                        "index": 0,
                        "finish_reason": "stop",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_async_chat_completion_with_system(
    async_client: AsyncOpenAI, span_exporter: InMemorySpanExporter
):
    """Test chat completion with system message and span verification."""
    response = await async_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant who speaks like a pirate.",
            },
            {"role": "user", "content": "What is the capital of France?"},
        ],
        temperature=0.7,
        max_tokens=100,
    )

    assert response.id
    assert response.choices
    assert response.choices[0].message.content
    assert (
        response.usage
        and response.usage.total_tokens <= 100 + response.usage.prompt_tokens
    )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gpt-4o-mini",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4o-mini",
                "gen_ai.request.temperature": 0.7,
                "gen_ai.request.max_tokens": 100,
                "server.address": "api.openai.com",
                "gen_ai.system": "openai",
                "gen_ai.response.model": "gpt-4o-mini-2024-07-18",
                "gen_ai.response.finish_reasons": ("stop",),
                "gen_ai.response.id": "chatcmpl-C3XPKltmZDKcldynQl8s0wMLYRDKl",
                "gen_ai.openai.request.service_tier": "default",
                "gen_ai.usage.input_tokens": 29,
                "gen_ai.usage.output_tokens": 25,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.system.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": "You are a helpful assistant who speaks like a pirate.",
                    },
                },
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": "What is the capital of France?",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "message": '{"role":"assistant","content":"Arrr, matey! The capital of France be Paris! A grand city o\' lights and romance, it be!"}',
                        "index": 0,
                        "finish_reason": "stop",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_streaming_chat_completion(
    client: OpenAI, span_exporter: InMemorySpanExporter
):
    """Test streaming chat completion with span verification."""
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Count to 3"}],
        stream=True,
    )

    chunks = []
    for chunk in stream:
        chunks.append(chunk)

    assert len(chunks) > 0
    assert any(chunk.choices[0].delta.content for chunk in chunks if chunk.choices)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gpt-4o-mini",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4o-mini",
                "server.address": "api.openai.com",
                "gen_ai.system": "openai",
                "gen_ai.response.model": "gpt-4o-mini-2024-07-18",
                "gen_ai.response.id": "chatcmpl-C2IjQMIDb4wsN7RAS4yUy4SypFyHv",
                "gen_ai.openai.response.service_tier": "default",
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {"gen_ai.system": "openai", "content": "Count to 3"},
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "index": 0,
                        "finish_reason": "stop",
                        "message": '{"role": "assistant", "content": "1, 2, 3."}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_async_streaming_chat_completion(
    async_client: AsyncOpenAI, span_exporter: InMemorySpanExporter
):
    """Test async streaming with span verification."""
    stream = await async_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Count to 3"}],
        stream=True,
    )

    chunks = []
    async for chunk in stream:
        chunks.append(chunk)

    assert len(chunks) > 0
    assert any(chunk.choices[0].delta.content for chunk in chunks if chunk.choices)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gpt-4o-mini",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4o-mini",
                "server.address": "api.openai.com",
                "gen_ai.system": "openai",
                "gen_ai.response.model": "gpt-4o-mini-2024-07-18",
                "gen_ai.response.id": "chatcmpl-C2IjRrSL7E98KQlzfRfuGI5aQ5nxZ",
                "gen_ai.openai.response.service_tier": "default",
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {"gen_ai.system": "openai", "content": "Count to 3"},
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "index": 0,
                        "finish_reason": "stop",
                        "message": '{"role": "assistant", "content": "1, 2, 3."}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_parse_with_pydantic(client: OpenAI, span_exporter: InMemorySpanExporter):
    """Test parse method with Pydantic and span verification."""

    class CalendarEvent(BaseModel):
        name: str
        date: str
        participants: list[str]

    completion = client.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "Create a calendar event for a team meeting tomorrow with Alice and Bob",
            }
        ],
        response_format=CalendarEvent,
    )

    assert completion.choices[0].message.parsed
    event = completion.choices[0].message.parsed
    assert isinstance(event, CalendarEvent)
    assert event.name
    assert event.date
    assert len(event.participants) > 0

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gpt-4o-mini",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4o-mini",
                "gen_ai.openai.request.response_format": "CalendarEvent",
                "server.address": "api.openai.com",
                "gen_ai.system": "openai",
                "gen_ai.response.model": "gpt-4o-mini-2024-07-18",
                "gen_ai.response.finish_reasons": ("stop",),
                "gen_ai.response.id": "chatcmpl-C2IjSMomIC8AFjTivof4kdEKgrZ0i",
                "gen_ai.openai.request.service_tier": "default",
                "gen_ai.usage.input_tokens": 88,
                "gen_ai.usage.output_tokens": 22,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": "Create a calendar event for a team meeting tomorrow with Alice and Bob",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "message": '{"role":"assistant","content":"{\\"name\\":\\"Team Meeting\\",\\"date\\":\\"2023-10-07\\",\\"participants\\":[\\"Alice\\",\\"Bob\\"]}"}',
                        "index": 0,
                        "finish_reason": "stop",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_async_parse_with_pydantic(
    async_client: AsyncOpenAI, span_exporter: InMemorySpanExporter
):
    """Test async parse with span verification."""

    class CalendarEvent(BaseModel):
        name: str
        date: str
        participants: list[str]

    completion = await async_client.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "Create a calendar event for a team meeting tomorrow with Alice and Bob",
            }
        ],
        response_format=CalendarEvent,
    )

    assert completion.choices[0].message.parsed
    event = completion.choices[0].message.parsed
    assert isinstance(event, CalendarEvent)
    assert event.name
    assert event.date
    assert len(event.participants) > 0

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gpt-4o-mini",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4o-mini",
                "gen_ai.openai.request.response_format": "CalendarEvent",
                "server.address": "api.openai.com",
                "gen_ai.system": "openai",
                "gen_ai.response.model": "gpt-4o-mini-2024-07-18",
                "gen_ai.response.finish_reasons": ("stop",),
                "gen_ai.response.id": "chatcmpl-C2IjTSY7KddHaiiB073IYloOY1C6V",
                "gen_ai.openai.request.service_tier": "default",
                "gen_ai.usage.input_tokens": 88,
                "gen_ai.usage.output_tokens": 22,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": "Create a calendar event for a team meeting tomorrow with Alice and Bob",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "message": '{"role":"assistant","content":"{\\"name\\":\\"Team Meeting\\",\\"date\\":\\"2023-10-06\\",\\"participants\\":[\\"Alice\\",\\"Bob\\"]}"}',
                        "index": 0,
                        "finish_reason": "stop",
                    },
                },
            ],
        }
    )


def test_preserves_method_signatures():
    """Test that instrumentation preserves original method signatures."""
    fresh_client = OpenAI(api_key="test")
    original_create_sig = inspect.signature(fresh_client.chat.completions.create)
    original_parse_sig = inspect.signature(fresh_client.chat.completions.parse)

    instrumented_client = OpenAI(api_key="test")
    instrument_openai(instrumented_client)

    assert (
        inspect.signature(instrumented_client.chat.completions.create)
        == original_create_sig
    )
    assert (
        inspect.signature(instrumented_client.chat.completions.parse)
        == original_parse_sig
    )


def test_multiple_clients_independent(api_key: str):
    """Test that multiple clients can be instrumented independently."""

    client1 = OpenAI(api_key=api_key)
    client2 = OpenAI(api_key=api_key)

    assert not isinstance(client1.chat.completions.create, FunctionWrapper)
    assert not isinstance(client1.chat.completions.parse, FunctionWrapper)
    assert not isinstance(client2.chat.completions.create, FunctionWrapper)
    assert not isinstance(client2.chat.completions.parse, FunctionWrapper)

    instrument_openai(client1)

    assert isinstance(client1.chat.completions.create, FunctionWrapper)
    assert isinstance(client1.chat.completions.parse, FunctionWrapper)

    assert not isinstance(client2.chat.completions.create, FunctionWrapper)
    assert not isinstance(client2.chat.completions.parse, FunctionWrapper)


@pytest.mark.vcr()
def test_error_handling(client: OpenAI, span_exporter: InMemorySpanExporter):
    """Test error handling and span error recording."""
    with pytest.raises(NotFoundError):
        client.chat.completions.create(
            model="invalid-model-name",
            messages=[{"role": "user", "content": "Hello"}],
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat invalid-model-name",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "invalid-model-name",
                "server.address": "api.openai.com",
                "gen_ai.system": "openai",
                "error.type": "NotFoundError",
            },
            "status": {
                "status_code": "ERROR",
                "description": "Error code: 404 - {'error': {'message': 'The model `invalid-model-name` does not exist or you do not have access to it.', 'type': 'invalid_request_error', 'param': None, 'code': 'model_not_found'}}",
            },
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {"gen_ai.system": "openai", "content": "Hello"},
                }
            ],
        }
    )


def test_client_marked_as_instrumented():
    """Test that client is marked as instrumented after instrumentation."""
    client = OpenAI(api_key="test")

    assert not hasattr(client, "_lilypad_instrumented")

    instrument_openai(client)

    assert hasattr(client, "_lilypad_instrumented")
    assert client._lilypad_instrumented is True  # pyright: ignore[reportAttributeAccessIssue]


def test_instrumentation_idempotent():
    """Test that instrumentation is truly idempotent."""
    client = OpenAI(api_key="test")

    instrument_openai(client)
    first_create = client.chat.completions.create
    first_parse = client.chat.completions.parse

    instrument_openai(client)
    second_create = client.chat.completions.create
    second_parse = client.chat.completions.parse

    assert second_create is first_create
    assert second_parse is first_parse


def test_async_instrumentation_idempotent():
    """Test that async instrumentation is truly idempotent."""
    client = AsyncOpenAI(api_key="test")

    instrument_openai(client)
    first_create = client.chat.completions.create
    first_parse = client.chat.completions.parse

    instrument_openai(client)
    second_create = client.chat.completions.create
    second_parse = client.chat.completions.parse

    assert second_create is first_create
    assert second_parse is first_parse


def test_preserves_async_nature():
    """Test that async methods remain async after patching."""
    from pydantic import BaseModel

    class TestResponse(BaseModel):
        test: str

    client = AsyncOpenAI(api_key="test")

    create_result_before = client.chat.completions.create(model="test", messages=[])
    parse_result_before = client.chat.completions.parse(
        model="test", messages=[], response_format=TestResponse
    )
    assert inspect.iscoroutine(create_result_before)
    assert inspect.iscoroutine(parse_result_before)
    create_result_before.close()
    parse_result_before.close()

    instrument_openai(client)

    create_result_after = client.chat.completions.create(model="test", messages=[])
    parse_result_after = client.chat.completions.parse(
        model="test", messages=[], response_format=TestResponse
    )
    assert inspect.iscoroutine(create_result_after)
    assert inspect.iscoroutine(parse_result_after)
    create_result_after.close()
    parse_result_after.close()
