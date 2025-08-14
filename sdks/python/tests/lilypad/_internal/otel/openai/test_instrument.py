"""Tests for OpenAI instrumentation."""

import os
import inspect
from unittest.mock import Mock, patch
from importlib.metadata import PackageNotFoundError

import pytest
from wrapt import FunctionWrapper
from dotenv import load_dotenv
from openai import (
    OpenAI,
    AsyncOpenAI,
    NotFoundError,
    APIStatusError,
    RateLimitError,
    APIConnectionError,
)
from pydantic import BaseModel
from inline_snapshot import snapshot
from openai.types.chat import ChatCompletion
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from lilypad._internal.otel.openai.instrument import instrument_openai

from ..test_utils import (
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
def test_sync_chat_completion_simple(
    client: OpenAI, span_exporter: InMemorySpanExporter
) -> None:
    """Test basic chat completion with span verification."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello, say 'Hi' back to me"}],
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
) -> None:
    """Test async chat completion with span verification."""
    response = await async_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello, say 'Hi' back to me"}],
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
) -> None:
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

    assert isinstance(response, ChatCompletion)
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
def test_sync_chat_completion_with_tools(
    client: OpenAI, span_exporter: InMemorySpanExporter
) -> None:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What's the weather in Tokyo today?"}],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get today's weather report",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "City and country e.g. Bogotá, Colombia",
                            },
                            "units": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"],
                                "description": "Units the temperature will be returned in.",
                            },
                        },
                        "required": ["location", "units"],
                        "additionalProperties": False,
                    },
                },
            }
        ],
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
                "gen_ai.system": "openai",
                "gen_ai.response.model": "gpt-4o-mini-2024-07-18",
                "gen_ai.response.finish_reasons": ("tool_calls",),
                "gen_ai.response.id": "chatcmpl-C3XhNKgmTCR5hS0CSl5qATizQP87Y",
                "gen_ai.openai.request.service_tier": "default",
                "gen_ai.usage.input_tokens": 79,
                "gen_ai.usage.output_tokens": 21,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": "What's the weather in Tokyo today?",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "message": '{"role":"assistant","tool_calls":[{"function":{"arguments":"{\\"location\\":\\"Tokyo, Japan\\",\\"units\\":\\"celsius\\"}","name":"get_weather"},"id":"call_QsfqVdAAIGjpAmWZOkYtPUIY","type":"function"}]}',
                        "index": 0,
                        "finish_reason": "tool_calls",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_streaming_chat_completion(
    client: OpenAI, span_exporter: InMemorySpanExporter
) -> None:
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
                "gen_ai.response.finish_reasons": ("stop",),
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
) -> None:
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
                "gen_ai.response.finish_reasons": ("stop",),
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
def test_sync_streaming_chat_completion_with_tools(
    client: OpenAI, span_exporter: InMemorySpanExporter
) -> None:
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What's the weather in Tokyo today?"}],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get today's weather report",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "City and country e.g. Bogotá, Colombia",
                            },
                            "units": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"],
                                "description": "Units the temperature will be returned in.",
                            },
                        },
                        "required": ["location", "units"],
                        "additionalProperties": False,
                    },
                },
            }
        ],
        stream=True,
    )

    chunks = []
    for chunk in stream:
        chunks.append(chunk)

    assert len(chunks) > 0

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
                "gen_ai.response.id": "chatcmpl-C3ZNmCTxVz6gr1eQLl32BjSeKbXsS",
                "gen_ai.openai.response.service_tier": "default",
                "gen_ai.response.finish_reasons": ("tool_calls",),
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": "What's the weather in Tokyo today?",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "message": '{"role": "assistant", "tool_calls": [{"id": "call_hPd1P1Cs6Dv0a5XvrE6MZQoi", "type": "function", "function": {"name": "get_weather", "arguments": "{\\"location\\":\\"Tokyo, Japan\\",\\"units\\":\\"celsius\\"}"}}]}',
                        "index": 0,
                        "finish_reason": "tool_calls",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_parse_with_pydantic(
    client: OpenAI, span_exporter: InMemorySpanExporter
) -> None:
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
) -> None:
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


def test_preserves_method_signatures() -> None:
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


def test_multiple_clients_independent(openai_api_key: str) -> None:
    """Test that multiple clients can be instrumented independently."""

    client1 = OpenAI(api_key=openai_api_key)
    client2 = OpenAI(api_key=openai_api_key)

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
def test_tool_message_with_tool_call_id(
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
                "gen_ai.response.id": "chatcmpl-C3ePBKySN70rmIC2xHDuxhkqbJP3u",
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
                        "tool_calls": '[{"function":{"name":"calculate","arguments":"{\\"expression\\": \\"2+2\\"}"},"id":"call_test123","type":"function"}]',
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
                        "message": '{"role":"assistant","content":"2 + 2 equals 4."}',
                        "index": 0,
                        "finish_reason": "stop",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_error_handling(client: OpenAI, span_exporter: InMemorySpanExporter) -> None:
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


def test_client_marked_as_instrumented() -> None:
    """Test that client is marked as instrumented after instrumentation."""
    client = OpenAI(api_key="test")

    assert not hasattr(client, "_lilypad_instrumented")

    instrument_openai(client)

    assert hasattr(client, "_lilypad_instrumented")
    assert client._lilypad_instrumented is True  # pyright: ignore[reportAttributeAccessIssue]


def test_instrumentation_idempotent() -> None:
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


def test_async_instrumentation_idempotent() -> None:
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


def test_preserves_async_nature() -> None:
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


def test_sync_chat_completion_api_connection_error(
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test sync chat completion with APIConnectionError."""
    mock_client = Mock(spec=OpenAI)

    mock_request = Mock()
    mock_request.url = "https://api.openai.com/v1/chat/completions"

    original_create = Mock(
        side_effect=APIConnectionError(
            message="Connection failed", request=mock_request
        )
    )
    mock_client.chat.completions.create = original_create

    instrument_openai(mock_client)

    with pytest.raises(APIConnectionError):
        mock_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gpt-4o-mini",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4o-mini",
                "gen_ai.system": "openai",
                "error.type": "APIConnectionError",
            },
            "status": {
                "status_code": "ERROR",
                "description": "Connection failed",
            },
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": "Hello",
                    },
                }
            ],
        }
    )


@pytest.mark.asyncio
async def test_async_chat_completion_api_connection_error(
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test async chat completion with APIConnectionError."""
    mock_client = Mock(spec=AsyncOpenAI)

    async def create_error(*args, **kwargs):
        mock_request = Mock()
        mock_request.url = "https://api.openai.com/v1/chat/completions"
        raise APIConnectionError(message="Connection failed", request=mock_request)

    original_create = Mock(side_effect=create_error)
    mock_client.chat.completions.create = original_create

    instrument_openai(mock_client)

    with pytest.raises(APIConnectionError):
        await mock_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gpt-4o-mini",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4o-mini",
                "gen_ai.system": "openai",
                "error.type": "APIConnectionError",
            },
            "status": {
                "status_code": "ERROR",
                "description": "Connection failed",
            },
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": "Hello",
                    },
                }
            ],
        }
    )


def test_sync_parse_rate_limit_error(span_exporter: InMemorySpanExporter) -> None:
    """Test sync parse with RateLimitError."""
    mock_client = Mock(spec=OpenAI)

    original_parse = Mock(
        side_effect=RateLimitError(
            message="Rate limit exceeded",
            response=Mock(status_code=429),
            body={"error": {"message": "Rate limit exceeded"}},
        )
    )
    mock_client.chat.completions.parse = original_parse

    instrument_openai(mock_client)

    class TestModel(BaseModel):
        test: str

    with pytest.raises(RateLimitError):
        mock_client.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            response_format=TestModel,
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gpt-4o-mini",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4o-mini",
                "gen_ai.openai.request.response_format": "TestModel",
                "gen_ai.system": "openai",
                "error.type": "RateLimitError",
            },
            "status": {
                "status_code": "ERROR",
                "description": "Rate limit exceeded",
            },
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": "Hello",
                    },
                }
            ],
        }
    )


@pytest.mark.asyncio
async def test_async_parse_rate_limit_error(
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test async parse with RateLimitError."""
    mock_client = Mock(spec=AsyncOpenAI)

    async def parse_error(*args, **kwargs):
        raise RateLimitError(
            message="Rate limit exceeded",
            response=Mock(status_code=429),
            body={"error": {"message": "Rate limit exceeded"}},
        )

    original_parse = Mock(side_effect=parse_error)
    mock_client.chat.completions.parse = original_parse

    instrument_openai(mock_client)

    class TestModel(BaseModel):
        test: str

    with pytest.raises(RateLimitError):
        await mock_client.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            response_format=TestModel,
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gpt-4o-mini",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4o-mini",
                "gen_ai.openai.request.response_format": "TestModel",
                "gen_ai.system": "openai",
                "error.type": "RateLimitError",
            },
            "status": {
                "status_code": "ERROR",
                "description": "Rate limit exceeded",
            },
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": "Hello",
                    },
                }
            ],
        }
    )


def test_sync_streaming_api_status_error(span_exporter: InMemorySpanExporter) -> None:
    """Test sync streaming with APIStatusError."""
    mock_client = Mock(spec=OpenAI)

    original_create = Mock(
        side_effect=APIStatusError(
            message="Internal server error",
            response=Mock(status_code=500),
            body={"error": {"message": "Internal server error"}},
        )
    )
    mock_client.chat.completions.create = original_create

    instrument_openai(mock_client)

    with pytest.raises(APIStatusError):
        mock_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            stream=True,
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gpt-4o-mini",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4o-mini",
                "gen_ai.system": "openai",
                "error.type": "APIStatusError",
            },
            "status": {
                "status_code": "ERROR",
                "description": "Internal server error",
            },
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": "Hello",
                    },
                }
            ],
        }
    )


def test_sync_wrapping_failure_create(
    caplog: pytest.LogCaptureFixture,
    readonly_mock: Mock,
) -> None:
    """Test sync client when wrapping create method fails."""
    mock_client = Mock(spec=OpenAI)
    mock_client.chat.completions = readonly_mock

    with caplog.at_level("WARNING"):
        instrument_openai(mock_client)

    assert hasattr(mock_client, "_lilypad_instrumented")
    assert mock_client._lilypad_instrumented is True
    assert "Failed to wrap Completions.create: AttributeError" in caplog.text


def test_sync_wrapping_failure_parse(
    caplog: pytest.LogCaptureFixture,
    partial_readonly_mock: Mock,
) -> None:
    """Test sync client when wrapping parse method fails."""
    mock_client = Mock(spec=OpenAI)
    mock_client.chat.completions = partial_readonly_mock

    with caplog.at_level("WARNING"):
        instrument_openai(mock_client)

    assert hasattr(mock_client, "_lilypad_instrumented")
    assert mock_client._lilypad_instrumented is True
    assert "Failed to wrap Completions.parse: AttributeError" in caplog.text


@pytest.mark.asyncio
async def test_async_wrapping_failure_create(
    caplog: pytest.LogCaptureFixture,
    readonly_mock: Mock,
) -> None:
    """Test async client when wrapping create method fails."""
    mock_client = Mock(spec=AsyncOpenAI)
    mock_client.chat.completions = readonly_mock

    with caplog.at_level("WARNING"):
        instrument_openai(mock_client)

    assert hasattr(mock_client, "_lilypad_instrumented")
    assert mock_client._lilypad_instrumented is True
    assert "Failed to wrap AsyncCompletions.create: AttributeError" in caplog.text


@pytest.mark.asyncio
async def test_async_wrapping_failure_parse(
    caplog: pytest.LogCaptureFixture,
    partial_readonly_mock: Mock,
) -> None:
    """Test async client when wrapping parse method fails."""
    mock_client = Mock(spec=AsyncOpenAI)
    mock_client.chat.completions = partial_readonly_mock

    with caplog.at_level("WARNING"):
        instrument_openai(mock_client)

    assert hasattr(mock_client, "_lilypad_instrumented")
    assert mock_client._lilypad_instrumented is True
    assert "Failed to wrap AsyncCompletions.parse: AttributeError" in caplog.text


def test_sync_partial_wrapping_failure(
    caplog: pytest.LogCaptureFixture,
    partial_readonly_mock: Mock,
) -> None:
    """Test sync client when only parse wrapping fails, create should still be wrapped."""
    mock_client = Mock(spec=OpenAI)
    mock_client.chat.completions = partial_readonly_mock

    with caplog.at_level("WARNING"):
        instrument_openai(mock_client)

    assert hasattr(mock_client, "_lilypad_instrumented")
    assert mock_client._lilypad_instrumented is True
    assert isinstance(mock_client.chat.completions.create, FunctionWrapper)
    assert "Failed to wrap Completions.parse: AttributeError" in caplog.text


def test_package_not_found_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test handling of PackageNotFoundError when determining lilypad-sdk version."""

    with patch(
        "lilypad._internal.otel.openai.instrument.version",
        side_effect=PackageNotFoundError("Package lilypad-sdk not found"),
    ):
        mock_client = Mock(spec=OpenAI)

        with caplog.at_level("DEBUG"):
            instrument_openai(mock_client)

        assert hasattr(mock_client, "_lilypad_instrumented")
        assert mock_client._lilypad_instrumented is True
        assert "Could not determine lilypad-sdk version" in caplog.text
        assert isinstance(mock_client.chat.completions.create, FunctionWrapper)
        assert isinstance(mock_client.chat.completions.parse, FunctionWrapper)


@pytest.mark.vcr()
def test_sync_streaming_with_usage(
    client: OpenAI, span_exporter: InMemorySpanExporter
) -> None:
    """Test streaming with usage information enabled."""
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello"}],
        stream=True,
        stream_options={"include_usage": True},
    )

    chunks = []
    for chunk in stream:
        chunks.append(chunk)

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
                "gen_ai.response.id": "chatcmpl-C3dWNVMQnBtnziHMFBczZApO4CVcQ",
                "gen_ai.openai.response.service_tier": "default",
                "gen_ai.usage.input_tokens": 9,
                "gen_ai.usage.output_tokens": 9,
                "gen_ai.response.finish_reasons": ("stop",),
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {"gen_ai.system": "openai", "content": "Say hello"},
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "index": 0,
                        "finish_reason": "stop",
                        "message": '{"role": "assistant", "content": "Hello! How can I assist you today?"}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_user_structured_content_is_jsonified(
    client: OpenAI, span_exporter: InMemorySpanExporter
) -> None:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Reply with OK"},
                ],
            }
        ],
        max_tokens=5,
    )
    assert isinstance(response, ChatCompletion)

    spans = span_exporter.get_finished_spans()
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gpt-4o-mini",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4o-mini",
                "gen_ai.request.max_tokens": 5,
                "server.address": "api.openai.com",
                "gen_ai.system": "openai",
                "gen_ai.response.model": "gpt-4o-mini-2024-07-18",
                "gen_ai.response.finish_reasons": ("stop",),
                "gen_ai.response.id": "chatcmpl-C3gyxiSITd8HBvUUx6opELU2TMj1k",
                "gen_ai.openai.request.service_tier": "default",
                "gen_ai.usage.input_tokens": 10,
                "gen_ai.usage.output_tokens": 1,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "content": '[{"type":"text","text":"Reply with OK"}]',
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "openai",
                        "message": '{"role":"assistant","content":"OK"}',
                        "index": 0,
                        "finish_reason": "stop",
                    },
                },
            ],
        }
    )
