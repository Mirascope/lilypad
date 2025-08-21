"""Tests for Anthropic instrumentation."""

import os

import pytest
from anthropic import Anthropic, AsyncAnthropic
from anthropic.types import Message, TextBlock, ToolUseBlock
from dotenv import load_dotenv
from inline_snapshot import snapshot
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from lilypad._internal.otel._utils import InstrumentedClient
from lilypad._internal.otel.anthropic import instrument_anthropic

from .test_utils import (
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
def test_anthropic_simple(
    client: Anthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test basic message creation with span verification."""
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        system="You are a helpful assistant who speaks like a pirate.",
        messages=[{"role": "user", "content": "Hello, say 'Hi' back to me"}],
        max_tokens=50,
    )

    assert isinstance(response, Message)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert (
        extract_span_data(spans[0])
        == snapshot(
            {
                "name": "chat claude-3-haiku-20240307",
                "attributes": {
                    "gen_ai.operation.name": "chat",
                    "gen_ai.request.model": "claude-3-haiku-20240307",
                    "gen_ai.request.max_tokens": 50,
                    "server.address": "api.anthropic.com",
                    "gen_ai.system": "anthropic",
                    "gen_ai.response.model": "claude-3-haiku-20240307",
                    "gen_ai.response.finish_reasons": ("max_tokens",),
                    "gen_ai.response.id": "msg_01MFf2ubMLgYA9HRC9p4CGrx",
                    "gen_ai.usage.input_tokens": 29,
                    "gen_ai.usage.output_tokens": 50,
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
                            "content": "Hello, say 'Hi' back to me",
                        },
                    },
                    {
                        "name": "gen_ai.choice",
                        "attributes": {
                            "gen_ai.system": "anthropic",
                            "message": '{"role":"assistant","content":"Ahoy, matey! Ye be speakin\' to the most scurvy-ridden pirate of the high seas. Avast, ye landlubber! *clears pirate-y throat* Ah"}',  # codespell:ignore speakin
                            "index": 0,
                            "finish_reason": "max_tokens",
                        },
                    },
                ],
            }
        )
    )


@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_async_anthropic_simple(
    async_client: AsyncAnthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test async message creation with span verification."""
    response = await async_client.messages.create(
        model="claude-3-haiku-20240307",
        system="You are a helpful assistant who speaks like a pirate.",
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
                "gen_ai.response.finish_reasons": ("max_tokens",),
                "gen_ai.response.id": "msg_01FEMUQUV6kDqyh8pS7SMNav",
                "gen_ai.usage.input_tokens": 29,
                "gen_ai.usage.output_tokens": 50,
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
                        "content": "Hello, say 'Hi' back to me",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "message": '{"role":"assistant","content":"Ahoy, matey! Avast ye, it be I, yer trusty pirate assistant. Shiver me timbers, \'tis a pleasure to make yer acquaintance. Yo ho ho an"}',
                        "index": 0,
                        "finish_reason": "max_tokens",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_anthropic_streaming(
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
                "gen_ai.response.id": "msg_013eVBuUgEL8uJqwpKk32kgP",
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
                        "message": '{"role":"assistant","content":"1, 2, 3."}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_async_anthropic_streaming(
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
                "gen_ai.response.id": "msg_011YutgMjUjMJuojwy296qQF",
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
                        "message": '{"role":"assistant","content":"1, 2, 3."}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_anthropic_streaming_with_context_manager(
    client: Anthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test streaming with `.stream` context manager"""
    stream_context_manager = client.messages.stream(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": "Hello, say 'Hi' back to me"}],
        max_tokens=200,
    )

    with stream_context_manager as stream:
        chunks = list(stream)
    assert len(chunks) > 0

    spans = span_exporter.get_finished_spans()
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat claude-3-5-sonnet-20241022",
            "attributes": {
                "gen_ai.system": "anthropic",
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-5-sonnet-20241022",
                "gen_ai.request.max_tokens": 200,
                "server.address": "api.anthropic.com",
                "gen_ai.response.id": "msg_01EVsHjET3nRHxwr1bbuxK96",
                "gen_ai.response.model": "claude-3-5-sonnet-20241022",
                "gen_ai.response.finish_reasons": ("end_turn",),
                "gen_ai.usage.input_tokens": 17,
                "gen_ai.usage.output_tokens": 10,
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
                        "index": 0,
                        "message": '{"role":"assistant","content":"Hi! How are you today?"}',
                        "finish_reason": "end_turn",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_async_anthropic_streaming_with_context_manager(
    async_client: AsyncAnthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test streaming with `.stream` context manager"""
    async_stream_context_manager = async_client.messages.stream(
        model="claude-3-5-sonnet-20241022",
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
            "name": "chat claude-3-5-sonnet-20241022",
            "attributes": {
                "gen_ai.system": "anthropic",
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "claude-3-5-sonnet-20241022",
                "gen_ai.request.max_tokens": 200,
                "server.address": "api.anthropic.com",
                "gen_ai.response.id": "msg_0148n4FQ8wNUD2Gsp1rqkgEf",
                "gen_ai.response.model": "claude-3-5-sonnet-20241022",
                "gen_ai.response.finish_reasons": ("end_turn",),
                "gen_ai.usage.input_tokens": 17,
                "gen_ai.usage.output_tokens": 9,
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
                        "index": 0,
                        "message": '{"role":"assistant","content":"Hi! How are you?"}',
                        "finish_reason": "end_turn",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_anthropic_tool_message_resinsertion(
    client: Anthropic, span_exporter: InMemorySpanExporter
) -> None:
    """Test message with tool use and tool result."""
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        messages=[
            {
                "role": "user",
                "content": [TextBlock(type="text", text="What is 2+2?")],
            },
            {
                "role": "assistant",
                "content": [
                    TextBlock(type="text", text="Let me run the calculation twice."),
                    {
                        "type": "tool_use",
                        "id": "toolu_test123",
                        "name": "calculate",
                        "input": {"expression": "2+2"},
                    },
                    ToolUseBlock(
                        id="toolu_test456",
                        name="calculate",
                        input={"expression": "2+2"},
                        type="tool_use",
                    ),
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_test123",
                        "content": "4",
                    },
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_test456",
                        "content": "4",
                    },
                ],
            },
            {
                "role": "assistant",
                "content": "The answer is 4!",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Awesome! What about 5+1?"},
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
                "gen_ai.response.id": "msg_01LgXWsyXxofdfwGDrGakeJR",
                "gen_ai.usage.input_tokens": 194,
                "gen_ai.usage.output_tokens": 20,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "What is 2+2?",
                    },
                },
                {
                    "name": "gen_ai.assistant.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "Let me run the calculation twice.",
                        "tool_calls": '[{"id":"toolu_test123","type":"function","function":{"name":"calculate","arguments":"{\\"expression\\":\\"2+2\\"}"}},{"id":"toolu_test456","type":"function","function":{"name":"calculate","arguments":"{\\"expression\\":\\"2+2\\"}"}}]',
                    },
                },
                {
                    "name": "gen_ai.user.message",
                    "attributes": {"gen_ai.system": "anthropic"},
                },
                {
                    "name": "gen_ai.tool.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "4",
                        "id": "toolu_test123",
                    },
                },
                {
                    "name": "gen_ai.tool.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "4",
                        "id": "toolu_test456",
                    },
                },
                {
                    "name": "gen_ai.assistant.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "The answer is 4!",
                    },
                },
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "content": "Awesome! What about 5+1?",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "anthropic",
                        "index": 0,
                        "message": '{"role":"assistant","content":"Okay, let\'s calculate 5+1:\\n\\n"}',
                        "finish_reason": "end_turn",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_anthropic_streaming_with_tools(
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
                "gen_ai.response.id": "msg_01R5YTQA3sFa8rg7c2fFhwYC",
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
                        "message": '{"role":"assistant","content":"I\'ll help you multiply 123 and 456 using the calculator tool."}',
                        "finish_reason": "tool_use",
                        "tool_calls": '[{"id":"toolu_01UkyykiM4YquEG1j4m4isWT","type":"function","function":{"name":"calculator","arguments":"\\"\\"\\"{\\\\\\"operation\\"\\"\\\\\\": \\\\\\"mul\\"\\"tiply\\\\\\"\\"\\", \\\\\\"a\\\\\\": 123\\"\\", \\\\\\"b\\\\\\"\\"\\": \\"\\"456}\\""}}]',
                    },
                },
            ],
        }
    )


def test_anthropic_instrumentation_idempotent() -> None:
    """Test that instrumentation is truly idempotent."""
    client = Anthropic(api_key="test")

    assert not isinstance(client, InstrumentedClient)

    instrument_anthropic(client)
    first_create = client.messages.create

    assert isinstance(client, InstrumentedClient)
    assert client.__lilypad_instrumented_client__

    instrument_anthropic(client)
    second_create = client.messages.create

    assert second_create is first_create
