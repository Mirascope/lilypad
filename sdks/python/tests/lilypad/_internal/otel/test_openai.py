"""Tests for OpenAI instrumentation."""

import os

import pytest
from dotenv import load_dotenv
from inline_snapshot import snapshot
from openai import (
    AsyncOpenAI,
    OpenAI,
)
from openai.types.chat import ChatCompletion
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pydantic import BaseModel

from lilypad._internal.otel._utils import client_is_already_instrumented
from lilypad._internal.otel.openai import instrument_openai

from .test_utils import (
    extract_span_data,
)


@pytest.fixture
def openai_api_key() -> str:
    """Get OpenAI API key from environment or return dummy key."""
    load_dotenv()
    return os.getenv("OPENAI_API_KEY", "test-api-key")


@pytest.fixture
def client(openai_api_key: str) -> OpenAI:
    """Create an instrumented OpenAI client."""
    client = OpenAI(api_key=openai_api_key)
    instrument_openai(client)
    return client


@pytest.fixture
def async_client(openai_api_key: str) -> AsyncOpenAI:
    """Create an instrumented AsyncOpenAI client."""
    client = AsyncOpenAI(api_key=openai_api_key)
    instrument_openai(client)
    return client


@pytest.mark.vcr()
def test_openai_simple(client: OpenAI, span_exporter: InMemorySpanExporter) -> None:
    """Test basic chat completion with span verification."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You greet people"},
            {"role": "user", "content": "Hello, say 'Hi' back to me"},
        ],
        stop="Hi!",
        service_tier="auto",
    )

    assert isinstance(response, ChatCompletion)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gpt-4o-mini",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4o-mini",
                "server.address": "api.openai.com",
                "gen_ai.request.stop_sequences": ("Hi!",),
                "gen_ai.system": "openai",
                "gen_ai.response.model": "gpt-4o-mini-2024-07-18",
                "gen_ai.response.finish_reasons": ("stop",),
                "gen_ai.response.id": "chatcmpl-C6vLqA1hIG2t4dfbEU6kmNvud81jq",
                "gen_ai.openai.request.service_tier": "default",
                "gen_ai.usage.input_tokens": 23,
                "gen_ai.usage.output_tokens": 2,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.system.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": "You greet people",
                    },
                },
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
                        "message": '{"content":"","role":"assistant"}',
                        "index": 0,
                        "finish_reason": "stop",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_async_openai_simple(
    async_client: AsyncOpenAI, span_exporter: InMemorySpanExporter
) -> None:
    """Test async chat completion with span verification."""
    response = await async_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You greet people"},
            {"role": "user", "content": "Hello, say 'Hi' back to me"},
        ],
        stop="Hi!",
        service_tier="auto",
    )

    assert isinstance(response, ChatCompletion)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gpt-4o-mini",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4o-mini",
                "server.address": "api.openai.com",
                "gen_ai.request.stop_sequences": ("Hi!",),
                "gen_ai.system": "openai",
                "gen_ai.response.model": "gpt-4o-mini-2024-07-18",
                "gen_ai.response.finish_reasons": ("stop",),
                "gen_ai.response.id": "chatcmpl-C6vLrheZ0ZCrGqchQ3XbGVpcR93wD",
                "gen_ai.openai.request.service_tier": "default",
                "gen_ai.usage.input_tokens": 23,
                "gen_ai.usage.output_tokens": 2,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.system.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": "You greet people",
                    },
                },
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
                        "message": '{"content":"","role":"assistant"}',
                        "index": 0,
                        "finish_reason": "stop",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_openai_streaming(client: OpenAI, span_exporter: InMemorySpanExporter) -> None:
    """Test streaming chat completion with span verification."""
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Count to 3"}],
        stream=True,
        stream_options={"include_usage": True},
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
                "gen_ai.response.id": "chatcmpl-C6vLrNWeuP6f9YHuvmgKFgTzBMSfY",
                "gen_ai.response.finish_reasons": ("stop",),
                "gen_ai.openai.request.service_tier": "default",
                "gen_ai.usage.input_tokens": 11,
                "gen_ai.usage.output_tokens": 8,
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
                        "message": '{"role":"assistant","content":"1, 2, 3."}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_async_openai_streaming(
    async_client: AsyncOpenAI, span_exporter: InMemorySpanExporter
) -> None:
    """Test async streaming with span verification."""
    stream = await async_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Count to 3"}],
        stream=True,
        stream_options={"include_usage": True},
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
                "gen_ai.response.id": "chatcmpl-C6vLsjJqnCKUP2xfVTx8k6KmlagiA",
                "gen_ai.response.finish_reasons": ("stop",),
                "gen_ai.openai.request.service_tier": "default",
                "gen_ai.usage.input_tokens": 11,
                "gen_ai.usage.output_tokens": 8,
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
                        "message": '{"role":"assistant","content":"1, 2, 3."}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_openai_parse(client: OpenAI, span_exporter: InMemorySpanExporter) -> None:
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
                "gen_ai.response.id": "chatcmpl-C6vLtC0DcZBzgdOOJQYlwLbOkkCqg",
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
                        "message": '{"content":"{\\"name\\":\\"Team Meeting\\",\\"date\\":\\"2023-10-26\\",\\"participants\\":[\\"Alice\\",\\"Bob\\"]}","role":"assistant"}',
                        "index": 0,
                        "finish_reason": "stop",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_openai_streaming_with_context_manager(
    client: OpenAI, span_exporter: InMemorySpanExporter
) -> None:
    """Test streaming with `.stream` context manager"""
    stream_context_manager = client.chat.completions.stream(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello, say 'Hi' back to me"}],
        max_tokens=200,
    )

    with stream_context_manager as stream:
        chunks = list(stream)
    assert len(chunks) > 0

    spans = span_exporter.get_finished_spans()
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gpt-4o-mini",
            "attributes": {
                "gen_ai.system": "openai",
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4o-mini",
                "gen_ai.request.max_tokens": 200,
                "server.address": "api.openai.com",
                "gen_ai.response.id": "chatcmpl-C75of9t9mw2bHivO4QXBrARF2bArh",
                "gen_ai.response.model": "gpt-4o-mini-2024-07-18",
                "gen_ai.response.finish_reasons": ("stop",),
                "gen_ai.openai.request.service_tier": "default",
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
                        "index": 0,
                        "message": '{"role":"assistant","content":"Hi! How can I assist you today?"}',
                        "finish_reason": "stop",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_async_openai_streaming_with_context_manager(
    async_client: AsyncOpenAI, span_exporter: InMemorySpanExporter
) -> None:
    """Test streaming with `.stream` context manager"""
    async_stream_context_manager = async_client.chat.completions.stream(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello, say 'Hi' back to me"}],
        max_tokens=200,
    )

    chunks = []
    async with async_stream_context_manager as stream:
        async for chunk in stream:
            chunks.append(chunk)
    assert len(chunks) > 0

    spans = span_exporter.get_finished_spans()
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gpt-4o-mini",
            "attributes": {
                "gen_ai.system": "openai",
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4o-mini",
                "gen_ai.request.max_tokens": 200,
                "server.address": "api.openai.com",
                "gen_ai.response.id": "chatcmpl-C75q393ZLGsfaJfHN5jgzJm4jyUGU",
                "gen_ai.response.model": "gpt-4o-mini-2024-07-18",
                "gen_ai.response.finish_reasons": ("stop",),
                "gen_ai.openai.request.service_tier": "default",
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
                        "index": 0,
                        "message": '{"role":"assistant","content":"Hi! How can I assist you today?"}',
                        "finish_reason": "stop",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_openai_tool_message_resinsertion(
    client: OpenAI, span_exporter: InMemorySpanExporter
) -> None:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "What's 2+2?"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_test123",
                        "type": "function",
                        "function": {
                            "name": "calculate",
                            "arguments": '{"expression": "2+2"}',
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "content": "4",
                "tool_call_id": "call_test123",
            },
        ],
    )

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
                "gen_ai.response.id": "chatcmpl-C6vLtTXAWxwqrXNQ75X8E7IZ6a293",
                "gen_ai.openai.request.service_tier": "default",
                "gen_ai.usage.input_tokens": 36,
                "gen_ai.usage.output_tokens": 8,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": "What's 2+2?",
                    },
                },
                {
                    "name": "gen_ai.assistant.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "tool_calls": '[{"id":"call_test123","type":"function","function":{"name":"calculate","arguments":"{\\"expression\\": \\"2+2\\"}"}}]',
                    },
                },
                {
                    "name": "gen_ai.tool.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": "4",
                        "id": "call_test123",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "message": '{"content":"2 + 2 equals 4.","role":"assistant"}',
                        "index": 0,
                        "finish_reason": "stop",
                    },
                },
            ],
        }
    )


def test_openai_instrumentation_idempotent() -> None:
    """Test that instrumentation is truly idempotent."""
    client = OpenAI(api_key="test")

    assert not client_is_already_instrumented(client)

    instrument_openai(client)
    first_create = client.chat.completions.create
    first_parse = client.chat.completions.parse

    assert client_is_already_instrumented(client)

    instrument_openai(client)
    second_create = client.chat.completions.create
    second_parse = client.chat.completions.parse

    assert second_create is first_create
    assert second_parse is first_parse
