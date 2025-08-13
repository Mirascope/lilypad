"""Tests for Anthropic instrumentation."""

import os
import inspect
from unittest.mock import Mock, patch
from importlib.metadata import PackageNotFoundError

import pytest
from wrapt import FunctionWrapper
from dotenv import load_dotenv
from anthropic import (
    Anthropic,
    NotFoundError,
    APIStatusError,
    AsyncAnthropic,
    RateLimitError,
    APIConnectionError,
)
from anthropic.types import Message
from inline_snapshot import snapshot
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from lilypad._internal.otel.anthropic.instrument import instrument_anthropic

from ..test_utils import (
    extract_span_data,
)


@pytest.fixture
def anthropic_api_key() -> str:
    """Get Anthropic API key from environment or return dummy key."""
    load_dotenv()
    return os.getenv("ANTHROPIC_API_KEY", "test-api-key")


@pytest.fixture
def client(anthropic_api_key: str) -> Anthropic:
    """Create an instrumented Anthropic client."""
    client = Anthropic(api_key=anthropic_api_key)
    instrument_anthropic(client)
    return client


@pytest.fixture
def async_client(anthropic_api_key: str) -> AsyncAnthropic:
    """Create an instrumented AsyncAnthropic client."""
    client = AsyncAnthropic(api_key=anthropic_api_key)
    instrument_anthropic(client)
    return client


@pytest.mark.vcr()
def test_sync_message_creation_simple(
    client: Anthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test basic message creation with span verification."""
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        messages=[{"role": "user", "content": "Hello, say 'Hi' back to me"}],
        max_tokens=50,
    )

    assert isinstance(response, Message)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 50,
                "server.address": "api.anthropic.com",
                "gen_ai.system": "anthropic",
                "gen_ai.response.model": "claude-3-haiku-20240307",
                "gen_ai.response.finish_reasons": ("end_turn",),
                "gen_ai.response.id": "msg_01GoN4CFGyrKHQFCFArWNhZN",
                "gen_ai.usage.input_tokens": 17,
                "gen_ai.usage.output_tokens": 5,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "Hello, say 'Hi' back to me",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "message": '{"role":"assistant","content":"Hi!"}',
                        "index": 0,
                        "finish_reason": "end_turn",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_async_message_creation_simple(
    async_client: AsyncAnthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test async message creation with span verification."""
    response = await async_client.messages.create(
        model="claude-3-haiku-20240307",
        messages=[{"role": "user", "content": "Hello, say 'Hi' back to me"}],
        max_tokens=50,
    )

    assert isinstance(response, Message)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 50,
                "server.address": "api.anthropic.com",
                "gen_ai.system": "anthropic",
                "gen_ai.response.model": "claude-3-haiku-20240307",
                "gen_ai.response.finish_reasons": ("end_turn",),
                "gen_ai.response.id": "msg_015Fq3xPw6RmU71LSjn35meD",
                "gen_ai.usage.input_tokens": 17,
                "gen_ai.usage.output_tokens": 5,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "Hello, say 'Hi' back to me",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "message": '{"role":"assistant","content":"Hi!"}',
                        "index": 0,
                        "finish_reason": "end_turn",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_message_creation_with_system(
    client: Anthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test message creation with system prompt and span verification."""
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        system="You are a helpful assistant who speaks like a pirate.",
        messages=[{"role": "user", "content": "What is the capital of France?"}],
        temperature=0.7,
        max_tokens=100,
    )

    assert isinstance(response, Message)

    spans = span_exporter.get_finished_spans()
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.temperature": 0.7,
                "gen_ai.request.max_tokens": 100,
                "server.address": "api.anthropic.com",
                "gen_ai.system": "anthropic",
                "gen_ai.response.model": "claude-3-haiku-20240307",
                "gen_ai.response.finish_reasons": ("end_turn",),
                "gen_ai.response.id": "msg_01EzTijeZqgvMGAxb7KLV1YQ",
                "gen_ai.usage.input_tokens": 26,
                "gen_ai.usage.output_tokens": 26,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.system.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "You are a helpful assistant who speaks like a pirate.",
                    },
                },
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "What is the capital of France?",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "message": '{"role":"assistant","content":"Ahoy, me hearty! The capital o\' France be the scurvy city o\' Paris."}',
                        "finish_reason": "end_turn",
                        "index": 0,
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_message_creation_with_tools(
    client: Anthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test message creation with tools and span verification."""
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        messages=[{"role": "user", "content": "What's the weather in Tokyo today?"}],
        tools=[
            {
                "name": "get_weather",
                "description": "Get today's weather report",
                "input_schema": {
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
                },
            }
        ],
        max_tokens=200,
    )

    assert isinstance(response, Message)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 200,
                "server.address": "api.anthropic.com",
                "gen_ai.system": "anthropic",
                "gen_ai.response.model": "claude-3-haiku-20240307",
                "gen_ai.response.finish_reasons": ("tool_use",),
                "gen_ai.response.id": "msg_01BTTjwFEBmY7RLggFv1qSkA",
                "gen_ai.usage.input_tokens": 389,
                "gen_ai.usage.output_tokens": 85,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "What's the weather in Tokyo today?",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "message": '{"role":"assistant","content":"Okay, let\'s check the weather in Tokyo today:"}',
                        "finish_reason": "tool_use",
                        "index": 0,
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "message": '{"role":"assistant","tool_calls":[{"id":"toolu_01WdXDz7rayWqdvHoYbqv8hz","type":"function","function":{"name":"get_weather","arguments":"{\\"location\\":\\"Tokyo, Japan\\",\\"units\\":\\"celsius\\"}"}}]}',
                        "finish_reason": "tool_use",
                        "index": 1,
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_streaming_message_creation(
    client: Anthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test streaming message creation with span verification."""
    stream = client.messages.create(
        model="claude-3-haiku-20240307",
        messages=[{"role": "user", "content": "Count to 3"}],
        max_tokens=50,
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
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 50,
                "server.address": "api.anthropic.com",
                "gen_ai.system": "anthropic",
                "gen_ai.response.model": "claude-3-haiku-20240307",
                "gen_ai.response.id": "msg_01QorJUmt7CFdfYTNL225E1s",
                "gen_ai.response.finish_reasons": ("end_turn",),
                "gen_ai.usage.input_tokens": 11,
                "gen_ai.usage.output_tokens": 12,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "Count to 3",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "index": 0,
                        "finish_reason": "end_turn",
                        "message": '{"role": "assistant", "content": "1, 2, 3."}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_async_streaming_message_creation(
    async_client: AsyncAnthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test async streaming with span verification."""
    stream = await async_client.messages.create(
        model="claude-3-haiku-20240307",
        messages=[{"role": "user", "content": "Count to 3"}],
        max_tokens=50,
        stream=True,
    )

    chunks = []
    async for chunk in stream:
        chunks.append(chunk)

    assert len(chunks) > 0

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 50,
                "server.address": "api.anthropic.com",
                "gen_ai.system": "anthropic",
                "gen_ai.response.model": "claude-3-haiku-20240307",
                "gen_ai.response.id": "msg_012S7swkBWUBeEygZoEYh18Z",
                "gen_ai.response.finish_reasons": ("end_turn",),
                "gen_ai.usage.input_tokens": 11,
                "gen_ai.usage.output_tokens": 12,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "Count to 3",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "index": 0,
                        "finish_reason": "end_turn",
                        "message": '{"role": "assistant", "content": "1, 2, 3."}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_streaming_message_creation_with_tools(
    client: Anthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test streaming message creation with tools and span verification."""
    stream = client.messages.create(
        model="claude-3-haiku-20240307",
        messages=[{"role": "user", "content": "What's the weather in Tokyo today?"}],
        tools=[
            {
                "name": "get_weather",
                "description": "Get today's weather report",
                "input_schema": {
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
                },
            }
        ],
        max_tokens=200,
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
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 200,
                "server.address": "api.anthropic.com",
                "gen_ai.system": "anthropic",
                "gen_ai.response.model": "claude-3-haiku-20240307",
                "gen_ai.response.id": "msg_01UWHNFBLJLDBkSePZiWAuWW",
                "gen_ai.response.finish_reasons": ("tool_use",),
                "gen_ai.usage.input_tokens": 389,
                "gen_ai.usage.output_tokens": 87,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "What's the weather in Tokyo today?",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "index": 0,
                        "finish_reason": "tool_use",
                        "message": '{"role": "assistant", "content": "Okay, let me check the weather for you in Tokyo today:"}',
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "index": 1,
                        "finish_reason": "tool_use",
                        "message": '{"role": "assistant", "tool_calls": [{"id": "toolu_01DL5y2R7EpDetYdavzqrn9s", "type": "function", "function": {"name": "get_weather", "arguments": "{\\"location\\": \\"Tokyo, Japan\\", \\"units\\": \\"celsius\\"}"}}]}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_tool_message_with_tool_use_id(
    client: Anthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test message with tool use and tool result."""
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        messages=[
            {"role": "user", "content": "What's 2+2?"},
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_test123",
                        "name": "calculate",
                        "input": {"expression": "2+2"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_test123",
                        "content": "4",
                    }
                ],
            },
        ],
        max_tokens=100,
    )

    assert response.content
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 100,
                "server.address": "api.anthropic.com",
                "gen_ai.system": "anthropic",
                "gen_ai.response.model": "claude-3-haiku-20240307",
                "gen_ai.response.finish_reasons": ("end_turn",),
                "gen_ai.response.id": "msg_01MY8XWnMDGTHugXs7zNn1QA",
                "gen_ai.usage.input_tokens": 80,
                "gen_ai.usage.output_tokens": 18,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "What's 2+2?",
                    },
                },
                {
                    "name": "gen_ai.assistant.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "tool_calls": '[{"id":"toolu_test123","type":"function","function":{"name":"calculate","arguments":"{\\"expression\\":\\"2+2\\"}"}}]',
                    },
                },
                {
                    "name": "gen_ai.user.message",
                    "attributes": {"gen_ai.system": "anthropic"},
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "message": '{"role":"assistant","content":"The result of 2 + 2 is 4."}',
                        "index": 0,
                        "finish_reason": "end_turn",
                    },
                },
            ],
        }
    )


def test_preserves_method_signatures() -> None:
    """Test that instrumentation preserves original method signatures."""
    fresh_client = Anthropic(api_key="test")
    original_create_sig = inspect.signature(fresh_client.messages.create)

    instrumented_client = Anthropic(api_key="test")
    instrument_anthropic(instrumented_client)

    assert inspect.signature(instrumented_client.messages.create) == original_create_sig


def test_multiple_clients_independent(anthropic_api_key: str) -> None:
    """Test that multiple clients can be instrumented independently."""
    client1 = Anthropic(api_key=anthropic_api_key)
    client2 = Anthropic(api_key=anthropic_api_key)

    assert not isinstance(client1.messages.create, FunctionWrapper)
    assert not isinstance(client2.messages.create, FunctionWrapper)

    instrument_anthropic(client1)

    assert isinstance(client1.messages.create, FunctionWrapper)
    assert not isinstance(client2.messages.create, FunctionWrapper)


@pytest.mark.vcr()
def test_error_handling(client: Anthropic, span_exporter: InMemorySpanExporter) -> None:
    """Test error handling and span error recording."""
    with pytest.raises(NotFoundError):
        client.messages.create(
            model="invalid-model-name",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=50,
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat invalid-model-name",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "invalid-model-name",
                "gen_ai.request.max_tokens": 50,
                "server.address": "api.anthropic.com",
                "gen_ai.system": "anthropic",
                "error.type": "NotFoundError",
            },
            "status": {
                "status_code": "ERROR",
                "description": "Error code: 404 - {'type': 'error', 'error': {'type': 'not_found_error', 'message': 'model: invalid-model-name'}}",
            },
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {"gen_ai.system": "anthropic", "content": "Hello"},
                }
            ],
        }
    )


def test_client_marked_as_instrumented() -> None:
    """Test that client is marked as instrumented after instrumentation."""
    client = Anthropic(api_key="test")

    assert not hasattr(client, "_lilypad_instrumented")

    instrument_anthropic(client)

    assert hasattr(client, "_lilypad_instrumented")
    assert client._lilypad_instrumented is True  # pyright: ignore[reportAttributeAccessIssue]


def test_instrumentation_idempotent() -> None:
    """Test that instrumentation is truly idempotent."""
    client = Anthropic(api_key="test")

    instrument_anthropic(client)
    first_create = client.messages.create

    instrument_anthropic(client)
    second_create = client.messages.create

    assert second_create is first_create


def test_async_instrumentation_idempotent() -> None:
    """Test that async instrumentation is truly idempotent."""
    client = AsyncAnthropic(api_key="test")

    instrument_anthropic(client)
    first_create = client.messages.create

    instrument_anthropic(client)
    second_create = client.messages.create

    assert second_create is first_create


def test_preserves_async_nature() -> None:
    """Test that async methods remain async after patching."""
    client = AsyncAnthropic(api_key="test")

    create_result_before = client.messages.create(
        model="test", messages=[], max_tokens=10
    )
    assert inspect.iscoroutine(create_result_before)
    create_result_before.close()

    instrument_anthropic(client)

    create_result_after = client.messages.create(
        model="test", messages=[], max_tokens=10
    )
    assert inspect.iscoroutine(create_result_after)
    create_result_after.close()


def test_sync_message_creation_api_connection_error(
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test sync message creation with APIConnectionError."""
    mock_client = Mock(spec=Anthropic)

    mock_request = Mock()
    mock_request.url = "https://api.anthropic.com/v1/messages"

    original_create = Mock(
        side_effect=APIConnectionError(
            message="Connection failed", request=mock_request
        )
    )
    mock_client.messages.create = original_create

    instrument_anthropic(mock_client)

    with pytest.raises(APIConnectionError):
        mock_client.messages.create(
            model="claude-3-haiku-20240307",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=50,
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 50,
                "gen_ai.system": "anthropic",
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
                        "gen_ai.system": "anthropic",
                        "content": "Hello",
                    },
                }
            ],
        }
    )


@pytest.mark.asyncio
async def test_async_message_creation_api_connection_error(
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test async message creation with APIConnectionError."""
    mock_client = Mock(spec=AsyncAnthropic)

    async def create_error(*args, **kwargs):
        mock_request = Mock()
        mock_request.url = "https://api.anthropic.com/v1/messages"
        raise APIConnectionError(message="Connection failed", request=mock_request)

    original_create = Mock(side_effect=create_error)
    mock_client.messages.create = original_create

    instrument_anthropic(mock_client)

    with pytest.raises(APIConnectionError):
        await mock_client.messages.create(
            model="claude-3-haiku-20240307",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=50,
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 50,
                "gen_ai.system": "anthropic",
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
                        "gen_ai.system": "anthropic",
                        "content": "Hello",
                    },
                }
            ],
        }
    )


def test_sync_message_rate_limit_error(
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test sync message creation with RateLimitError."""
    mock_client = Mock(spec=Anthropic)

    original_create = Mock(
        side_effect=RateLimitError(
            message="Rate limit exceeded",
            response=Mock(status_code=429),
            body={"error": {"message": "Rate limit exceeded"}},
        )
    )
    mock_client.messages.create = original_create

    instrument_anthropic(mock_client)

    with pytest.raises(RateLimitError):
        mock_client.messages.create(
            model="claude-3-haiku-20240307",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=50,
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 50,
                "gen_ai.system": "anthropic",
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
                        "gen_ai.system": "anthropic",
                        "content": "Hello",
                    },
                }
            ],
        }
    )


@pytest.mark.asyncio
async def test_async_message_rate_limit_error(
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test async message creation with RateLimitError."""
    mock_client = Mock(spec=AsyncAnthropic)

    async def create_error(*args, **kwargs):
        raise RateLimitError(
            message="Rate limit exceeded",
            response=Mock(status_code=429),
            body={"error": {"message": "Rate limit exceeded"}},
        )

    original_create = Mock(side_effect=create_error)
    mock_client.messages.create = original_create

    instrument_anthropic(mock_client)

    with pytest.raises(RateLimitError):
        await mock_client.messages.create(
            model="claude-3-haiku-20240307",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=50,
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 50,
                "gen_ai.system": "anthropic",
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
                        "gen_ai.system": "anthropic",
                        "content": "Hello",
                    },
                }
            ],
        }
    )


def test_sync_streaming_api_status_error(
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test sync streaming with APIStatusError."""
    mock_client = Mock(spec=Anthropic)

    original_create = Mock(
        side_effect=APIStatusError(
            message="Internal server error",
            response=Mock(status_code=500),
            body={"error": {"message": "Internal server error"}},
        )
    )
    mock_client.messages.create = original_create

    instrument_anthropic(mock_client)

    with pytest.raises(APIStatusError):
        mock_client.messages.create(
            model="claude-3-haiku-20240307",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=50,
            stream=True,
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 50,
                "gen_ai.system": "anthropic",
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
                        "gen_ai.system": "anthropic",
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
    mock_client = Mock(spec=Anthropic)
    mock_client.messages = readonly_mock

    with caplog.at_level("WARNING"):
        instrument_anthropic(mock_client)

    assert hasattr(mock_client, "_lilypad_instrumented")
    assert mock_client._lilypad_instrumented is True
    assert "Failed to wrap Messages.create: AttributeError" in caplog.text


@pytest.mark.asyncio
async def test_async_wrapping_failure_create(
    caplog: pytest.LogCaptureFixture,
    readonly_mock: Mock,
) -> None:
    """Test async client when wrapping create method fails."""
    mock_client = Mock(spec=AsyncAnthropic)
    mock_client.messages = readonly_mock

    with caplog.at_level("WARNING"):
        instrument_anthropic(mock_client)

    assert hasattr(mock_client, "_lilypad_instrumented")
    assert mock_client._lilypad_instrumented is True
    assert "Failed to wrap AsyncMessages.create: AttributeError" in caplog.text


def test_package_not_found_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test handling of PackageNotFoundError when determining lilypad-sdk version."""
    with patch(
        "lilypad._internal.otel.anthropic.instrument.version",
        side_effect=PackageNotFoundError("Package lilypad-sdk not found"),
    ):
        mock_client = Mock(spec=Anthropic)

        with caplog.at_level("DEBUG"):
            instrument_anthropic(mock_client)

        assert hasattr(mock_client, "_lilypad_instrumented")
        assert mock_client._lilypad_instrumented is True
        assert "Could not determine lilypad-sdk version" in caplog.text
        assert isinstance(mock_client.messages.create, FunctionWrapper)


@pytest.mark.vcr()
def test_user_structured_content_is_jsonified(
    client: Anthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test that structured user content is properly JSONified in events."""
    response = client.messages.create(
        model="claude-3-haiku-20240307",
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
    assert isinstance(response, Message)

    spans = span_exporter.get_finished_spans()
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 5,
                "server.address": "api.anthropic.com",
                "gen_ai.system": "anthropic",
                "gen_ai.response.model": "claude-3-haiku-20240307",
                "gen_ai.response.finish_reasons": ("end_turn",),
                "gen_ai.response.id": "msg_01HvUTzuJrpuw4iM6JEVfCrg",
                "gen_ai.usage.input_tokens": 10,
                "gen_ai.usage.output_tokens": 4,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "Reply with OK",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "message": '{"role":"assistant","content":"OK"}',
                        "index": 0,
                        "finish_reason": "end_turn",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_message_with_advanced_params(
    client: Anthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test message creation with top_p, top_k, and stop_sequences parameters."""
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        messages=[{"role": "user", "content": "Count from 1 to 10"}],
        max_tokens=50,
        temperature=0.5,
        top_p=0.9,
        top_k=40,
        stop_sequences=["5", "STOP"],
    )

    assert isinstance(response, Message)

    spans = span_exporter.get_finished_spans()
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 50,
                "gen_ai.request.temperature": 0.5,
                "gen_ai.request.top_p": 0.9,
                "gen_ai.request.top_k": 40,
                "gen_ai.request.stop_sequences": ("5", "STOP"),
                "server.address": "api.anthropic.com",
                "gen_ai.system": "anthropic",
                "gen_ai.response.model": "claude-3-haiku-20240307",
                "gen_ai.response.finish_reasons": ("stop_sequence",),
                "gen_ai.response.id": "msg_01DNgVygQxNYvEasAop9YxPk",
                "gen_ai.usage.input_tokens": 15,
                "gen_ai.usage.output_tokens": 14,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "Count from 1 to 10",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "message": '{"role":"assistant","content":"1, 2, 3, 4, "}',
                        "index": 0,
                        "finish_reason": "stop_sequence",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_multiple_content_blocks_in_response(
    client: Anthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test response with multiple content blocks (text and tool use)."""
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        messages=[
            {
                "role": "user",
                "content": "Use the calculator to add 2+2, then explain the result",
            }
        ],
        tools=[
            {
                "name": "calculator",
                "description": "A simple calculator",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string", "enum": ["add", "subtract"]},
                        "a": {"type": "number"},
                        "b": {"type": "number"},
                    },
                    "required": ["operation", "a", "b"],
                },
            }
        ],
        max_tokens=200,
    )

    assert isinstance(response, Message)

    spans = span_exporter.get_finished_spans()
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 200,
                "server.address": "api.anthropic.com",
                "gen_ai.system": "anthropic",
                "gen_ai.response.model": "claude-3-haiku-20240307",
                "gen_ai.response.finish_reasons": ("tool_use",),
                "gen_ai.response.id": "msg_01KV2iLqmFG9x2eP5pUYjPov",
                "gen_ai.usage.input_tokens": 369,
                "gen_ai.usage.output_tokens": 85,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "Use the calculator to add 2+2, then explain the result",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "message": '{"role":"assistant","tool_calls":[{"id":"toolu_01YFd3xn1WU8TvvRaEZJo2A9","type":"function","function":{"name":"calculator","arguments":"{\\"a\\":2,\\"b\\":2,\\"operation\\":\\"add\\"}"}}]}',
                        "finish_reason": "tool_use",
                        "index": 0,
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_async_streaming_with_multiple_blocks(
    async_client: AsyncAnthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test async streaming with multiple content blocks."""
    stream = await async_client.messages.create(
        model="claude-3-haiku-20240307",
        messages=[
            {
                "role": "user",
                "content": "First say hello, then use a tool to get weather",
            }
        ],
        tools=[
            {
                "name": "get_weather",
                "description": "Get weather for a location",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"},
                    },
                    "required": ["location"],
                },
            }
        ],
        max_tokens=200,
        stream=True,
    )

    chunks = [chunk async for chunk in stream]
    assert len(chunks) > 0

    spans = span_exporter.get_finished_spans()
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 200,
                "server.address": "api.anthropic.com",
                "gen_ai.system": "anthropic",
                "gen_ai.response.model": "claude-3-haiku-20240307",
                "gen_ai.response.finish_reasons": ("tool_use",),
                "gen_ai.response.id": "msg_017g5nGzRt4EZ99PJCL3mPcV",
                "gen_ai.usage.input_tokens": 335,
                "gen_ai.usage.output_tokens": 56,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "First say hello, then use a tool to get weather",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "index": 0,
                        "finish_reason": "tool_use",
                        "message": '{"role": "assistant", "tool_calls": [{"id": "toolu_012Ve9LFLZeA5nuaqr4CXMrU", "type": "function", "function": {"name": "get_weather", "arguments": "{\\"location\\": \\"New York, NY\\"}"}}]}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_assistant_message_with_empty_content(
    client: Anthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test assistant message with empty content in conversation history."""
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        messages=[
            {"role": "user", "content": "What's 5+5?"},
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "tool_123",
                        "name": "calculator",
                        "input": {"operation": "add", "a": 5, "b": 5},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "tool_123",
                        "content": "10",
                    }
                ],
            },
        ],
        max_tokens=50,
    )

    assert isinstance(response, Message)

    spans = span_exporter.get_finished_spans()
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 50,
                "server.address": "api.anthropic.com",
                "gen_ai.system": "anthropic",
                "gen_ai.response.model": "claude-3-haiku-20240307",
                "gen_ai.response.finish_reasons": ("end_turn",),
                "gen_ai.response.id": "msg_01PnwR192aksf1WmLLjQnQ2z",
                "gen_ai.usage.input_tokens": 112,
                "gen_ai.usage.output_tokens": 18,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "What's 5+5?",
                    },
                },
                {
                    "name": "gen_ai.assistant.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "tool_calls": '[{"id":"tool_123","type":"function","function":{"name":"calculator","arguments":"{\\"operation\\":\\"add\\",\\"a\\":5,\\"b\\":5}"}}]',
                    },
                },
                {
                    "name": "gen_ai.user.message",
                    "attributes": {"gen_ai.system": "anthropic"},
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "message": '{"role":"assistant","content":"The result of 5 + 5 is 10."}',
                        "index": 0,
                        "finish_reason": "end_turn",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_streaming_with_stop_sequence(
    client: Anthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test streaming that stops due to stop sequence."""
    stream = client.messages.create(
        model="claude-3-haiku-20240307",
        messages=[{"role": "user", "content": "Count from 1 to 10"}],
        max_tokens=100,
        stop_sequences=["5"],
        stream=True,
    )

    chunks = list(stream)
    assert len(chunks) > 0

    spans = span_exporter.get_finished_spans()
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 100,
                "gen_ai.request.stop_sequences": ("5",),
                "server.address": "api.anthropic.com",
                "gen_ai.system": "anthropic",
                "gen_ai.response.model": "claude-3-haiku-20240307",
                "gen_ai.response.id": "msg_01MkwFJN43cbW1dV6aLXEoH9",
                "gen_ai.response.finish_reasons": ("stop_sequence",),
                "gen_ai.usage.input_tokens": 15,
                "gen_ai.usage.output_tokens": 14,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "Count from 1 to 10",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "index": 0,
                        "finish_reason": "stop_sequence",
                        "message": '{"role": "assistant", "content": "1, 2, 3, 4, "}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_structured_user_content_as_text(
    client: Anthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test that non-list user content is properly handled."""
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        messages=[
            {
                "role": "user",
                "content": "Simple text message",
            }
        ],
        max_tokens=5,
    )
    assert isinstance(response, Message)

    spans = span_exporter.get_finished_spans()
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 5,
                "server.address": "api.anthropic.com",
                "gen_ai.system": "anthropic",
                "gen_ai.response.model": "claude-3-haiku-20240307",
                "gen_ai.response.finish_reasons": ("max_tokens",),
                "gen_ai.response.id": "msg_01ULUU4JsTPuhYDUbYWp7Nfj",
                "gen_ai.usage.input_tokens": 10,
                "gen_ai.usage.output_tokens": 5,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "Simple text message",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "message": '{"role":"assistant","content":"Okay, I\'m"}',
                        "index": 0,
                        "finish_reason": "max_tokens",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_streaming_tool_use_detailed(
    client: Anthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test streaming with tool use to ensure input_json_delta events are captured."""
    stream = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[
            {"role": "user", "content": "Calculate 123 * 456 using the calculator tool"}
        ],
        tools=[
            {
                "name": "calculator",
                "description": "Performs basic arithmetic",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["multiply", "add", "subtract", "divide"],
                        },
                        "a": {"type": "number"},
                        "b": {"type": "number"},
                    },
                    "required": ["operation", "a", "b"],
                },
            }
        ],
        max_tokens=200,
        stream=True,
    )

    chunks = list(stream)
    assert len(chunks) > 0

    spans = span_exporter.get_finished_spans()
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-5-sonnet-20241022",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-5-sonnet-20241022",
                "gen_ai.request.max_tokens": 200,
                "server.address": "api.anthropic.com",
                "gen_ai.system": "anthropic",
                "gen_ai.response.model": "claude-3-5-sonnet-20241022",
                "gen_ai.response.id": "msg_01EP6EGGKpKQNgBtecdZ2RxB",
                "gen_ai.response.finish_reasons": ("tool_use",),
                "gen_ai.usage.input_tokens": 423,
                "gen_ai.usage.output_tokens": 103,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "Calculate 123 * 456 using the calculator tool",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "index": 0,
                        "finish_reason": "tool_use",
                        "message": '{"role": "assistant", "content": "I\'ll help you multiply 123 by 456 using the calculator tool."}',
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "index": 1,
                        "finish_reason": "tool_use",
                        "message": '{"role": "assistant", "tool_calls": [{"id": "toolu_01HfCf8ib3nRGcpqyyQ46gqF", "type": "function", "function": {"name": "calculator", "arguments": "{\\"operation\\": \\"multiply\\", \\"a\\": 123, \\"b\\": 456}"}}]}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_streaming_with_input_json_delta(
    client: Anthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test that input_json_delta chunks are properly processed during tool streaming."""
    stream = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": "Use the calculator to compute 42 * 17"}],
        tools=[
            {
                "name": "calculator",
                "description": "Performs calculations",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"},
                    },
                    "required": ["expression"],
                },
            }
        ],
        max_tokens=300,
        stream=True,
    )

    chunks = list(stream)
    assert len(chunks) > 0

    spans = span_exporter.get_finished_spans()
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-5-sonnet-20241022",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-5-sonnet-20241022",
                "gen_ai.request.max_tokens": 300,
                "server.address": "api.anthropic.com",
                "gen_ai.system": "anthropic",
                "gen_ai.response.model": "claude-3-5-sonnet-20241022",
                "gen_ai.response.id": "msg_01MVpyWMCxqqTBM4o9uyYJ49",
                "gen_ai.response.finish_reasons": ("tool_use",),
                "gen_ai.usage.input_tokens": 380,
                "gen_ai.usage.output_tokens": 75,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "Use the calculator to compute 42 * 17",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "index": 0,
                        "finish_reason": "tool_use",
                        "message": '{"role": "assistant", "content": "I\'ll help you calculate 42 multiplied by 17 using the calculator tool."}',
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "index": 1,
                        "finish_reason": "tool_use",
                        "message": '{"role": "assistant", "tool_calls": [{"id": "toolu_016GFtMEs6NRjMteg9c9fE4v", "type": "function", "function": {"name": "calculator", "arguments": "{\\"expression\\": \\"42 * 17\\"}"}}]}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_streaming_max_tokens_stop_reason(
    client: Anthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test streaming that stops due to max_tokens limit."""
    stream = client.messages.create(
        model="claude-3-haiku-20240307",
        messages=[{"role": "user", "content": "Write a very long story about a robot"}],
        max_tokens=10,
        stream=True,
    )

    chunks = list(stream)
    assert len(chunks) > 0

    spans = span_exporter.get_finished_spans()
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-haiku-20240307",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-haiku-20240307",
                "gen_ai.request.max_tokens": 10,
                "server.address": "api.anthropic.com",
                "gen_ai.system": "anthropic",
                "gen_ai.response.model": "claude-3-haiku-20240307",
                "gen_ai.response.id": "msg_018dfAvKYnjmrx6J8ppbmj5u",
                "gen_ai.response.finish_reasons": ("max_tokens",),
                "gen_ai.usage.input_tokens": 15,
                "gen_ai.usage.output_tokens": 10,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "Write a very long story about a robot",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "index": 0,
                        "finish_reason": "max_tokens",
                        "message": '{"role": "assistant", "content": "Here is a very long story about a robot:"}',
                    },
                },
            ],
        }
    )
