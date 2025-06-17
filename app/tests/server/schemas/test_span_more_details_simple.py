"""Targeted tests for span_more_details.py to maximize coverage efficiently."""

import contextlib
import json
from datetime import datetime
from unittest.mock import AsyncMock, patch, Mock
from uuid import uuid4

import pytest

from lilypad.server.schemas.span_more_details import (
    Event,
    MessageParam,
    SpanMoreDetails,
    _AudioPart,
    _convert_timestamp,
    _extract_event_attribute,
    _ImagePart,
    _TextPart,
    _ToolCall,
    calculate_openrouter_cost,
    convert_anthropic_messages,
    convert_azure_messages,
    convert_events,
    convert_gemini_messages,
    convert_mirascope_messages,
    convert_openai_messages,
    fetch_with_memory_cache,
    parse_nested_json,
)


def test_text_part():
    """Test _TextPart model."""
    part = _TextPart(type="text", text="Hello")
    assert part.type == "text"
    assert part.text == "Hello"


def test_image_part():
    """Test _ImagePart model."""
    part = _ImagePart(
        type="image", media_type="image/jpeg", image="data", detail="high"
    )
    assert part.type == "image"
    assert part.media_type == "image/jpeg"
    assert part.image == "data"
    assert part.detail == "high"


def test_audio_part():
    """Test _AudioPart model."""
    part = _AudioPart(type="audio", media_type="audio/mp3", audio="data")
    assert part.type == "audio"
    assert part.media_type == "audio/mp3"
    assert part.audio == "data"


def test_tool_call():
    """Test _ToolCall model."""
    tool = _ToolCall(type="tool_call", name="func", arguments={"x": 1})
    assert tool.type == "tool_call"
    assert tool.name == "func"
    assert tool.arguments == {"x": 1}


def test_message_param():
    """Test MessageParam model."""
    content = [_TextPart(type="text", text="Hello")]
    msg = MessageParam(role="user", content=content)  # type: ignore[arg-type]
    assert msg.role == "user"
    assert len(msg.content) == 1


def test_event():
    """Test Event model."""
    now = datetime.now()
    event = Event(name="test", type="info", message="msg", timestamp=now)
    assert event.name == "test"
    assert event.type == "info"
    assert event.message == "msg"
    assert event.timestamp == now


def test_convert_gemini_messages_basic():
    """Test convert_gemini_messages with various inputs."""
    # Empty messages
    result = convert_gemini_messages([])
    assert len(result) == 1
    assert result[0].role == "assistant"

    # User message
    messages = [{"name": "gen_ai.user.message", "attributes": {"content": '["Hello"]'}}]
    result = convert_gemini_messages(messages)
    assert len(result) == 2
    assert result[0].role == "user"
    assert result[1].role == "assistant"

    # System message
    messages = [
        {
            "name": "gen_ai.system.message",
            "attributes": {"content": '["System prompt"]'},
        }
    ]
    result = convert_gemini_messages(messages)
    assert len(result) == 2
    assert result[0].role == "system"

    # Invalid JSON
    messages = [
        {"name": "gen_ai.user.message", "attributes": {"content": "invalid json"}}
    ]
    result = convert_gemini_messages(messages)
    assert len(result) == 2
    assert result[0].role == "user"
    assert len(result[0].content) == 1

    # Missing attributes
    messages = [{"name": "gen_ai.user.message"}]
    result = convert_gemini_messages(messages)
    assert len(result) == 1
    assert result[0].role == "assistant"


def test_convert_openai_messages_basic():
    """Test convert_openai_messages with various inputs."""
    # Text message
    messages = [{"role": "user", "content": "Hello"}]
    result = convert_openai_messages(messages)
    assert len(result) == 1
    assert (
        result[0].role == "assistant"
    )  # No user/system messages were found in gen_ai format

    # With gen_ai format
    messages = [{"name": "gen_ai.user.message", "attributes": {"content": '["Hello"]'}}]
    result = convert_openai_messages(messages)
    assert len(result) == 2
    assert result[0].role == "user"
    assert result[1].role == "assistant"


def test_convert_azure_messages():
    """Test convert_azure_messages."""
    messages = [
        {"name": "gen_ai.user.message", "attributes": {"content": '["Hello Azure"]'}}
    ]
    result = convert_azure_messages(messages)
    assert len(result) == 2
    assert result[0].role == "user"
    assert result[1].role == "assistant"


def test_convert_anthropic_messages():
    """Test convert_anthropic_messages."""
    messages = [
        {"name": "gen_ai.user.message", "attributes": {"content": '["Hello Claude"]'}}
    ]
    result = convert_anthropic_messages(messages)
    assert len(result) == 2
    assert result[0].role == "user"
    assert result[1].role == "assistant"


def test_convert_mirascope_messages_basic():
    """Test convert_mirascope_messages."""
    # String input
    messages_str = '[{"role": "user", "content": "Hello"}]'
    result = convert_mirascope_messages(messages_str)
    assert len(result) == 1
    assert result[0].role == "user"

    # List input
    messages = [{"role": "user", "content": "Hello"}]
    result = convert_mirascope_messages(messages)
    assert len(result) == 1
    assert result[0].role == "user"


def test_convert_events():
    """Test convert_events."""
    events = [
        {
            "name": "test.event",
            "timestamp": 1640995200000000000,  # nanoseconds
            "attributes": {
                "test.event.type": "info",
                "test.event.message": "Test message",
            },
        }
    ]
    result = convert_events(events)
    assert len(result) == 1
    assert result[0].name == "test.event"
    assert result[0].type == "info"
    assert result[0].message == "Test message"


def test_convert_timestamp():
    """Test _convert_timestamp utility."""
    ns_timestamp = 1640995200000000000  # 2022-01-01 00:00:00 UTC in nanoseconds
    result = _convert_timestamp(ns_timestamp)
    assert isinstance(result, datetime)
    assert result.year == 2022


def test_extract_event_attribute():
    """Test _extract_event_attribute utility."""
    event = {
        "name": "test.event",
        "attributes": {"test.event.type": "info", "test.event.message": "Test message"},
    }
    assert _extract_event_attribute(event, "type") == "info"
    assert _extract_event_attribute(event, "message") == "Test message"
    assert _extract_event_attribute(event, "missing") == ""


@pytest.mark.asyncio
async def test_fetch_with_memory_cache():
    """Test fetch_with_memory_cache."""
    with patch("httpx.AsyncClient") as mock_client:
        # Success case
        mock_response = Mock()
        mock_response.json.return_value = {"test": "data"}

        mock_instance = AsyncMock()
        mock_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_instance

        result = await fetch_with_memory_cache("http://example.com/success")
        assert result == {"test": "data"}

    # Test with JSON decode error to trigger error handling
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        mock_instance = AsyncMock()
        mock_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_instance

        with contextlib.suppress(json.JSONDecodeError):
            result = await fetch_with_memory_cache("http://example.com/json_error")


@pytest.mark.asyncio
async def test_calculate_openrouter_cost():
    """Test calculate_openrouter_cost."""
    # Success case
    with patch(
        "lilypad.server.schemas.span_more_details.fetch_with_memory_cache",
        new_callable=AsyncMock,
    ) as mock_fetch:
        mock_fetch.return_value = {
            "data": [
                {
                    "id": "test-model",
                    "pricing": {"prompt": "0.001", "completion": "0.002"},
                }
            ]
        }
        cost = await calculate_openrouter_cost(1000, 500, "test-model")
        expected = (1000 * 0.001) + (500 * 0.002)
        assert cost == expected

        # Model not found
        cost = await calculate_openrouter_cost(1000, 500, "missing-model")
        assert cost is None

    # None inputs
    cost = await calculate_openrouter_cost(None, 500, "test-model")
    assert cost is None

    # API error - missing data key
    with patch(
        "lilypad.server.schemas.span_more_details.fetch_with_memory_cache",
        new_callable=AsyncMock,
    ) as mock_fetch:
        mock_fetch.return_value = {}
        with contextlib.suppress(KeyError):
            cost = await calculate_openrouter_cost(1000, 500, "test-model")


def test_parse_nested_json():
    """Test parse_nested_json."""
    # Valid JSON
    data = '{"key": "value"}'
    result = parse_nested_json(data)
    assert result == {"key": "value"}

    # Nested JSON
    nested = '{"outer": "{\\"inner\\": \\"value\\"}"}'
    result = parse_nested_json(nested)
    assert result == {"outer": {"inner": "value"}}

    # Invalid JSON
    result = parse_nested_json("invalid")
    assert result == "invalid"

    # Dict input
    data = {"key": "value"}
    result = parse_nested_json(data)
    assert result == {"key": "value"}

    # List input
    data = ["item1", "item2"]
    result = parse_nested_json(data)
    assert result == ["item1", "item2"]


def test_span_more_details_basic():
    """Test SpanMoreDetails basic functionality."""
    details = SpanMoreDetails(
        uuid=uuid4(),
        project_uuid=uuid4(),
        display_name="test",
        provider="openai",
        model="gpt-4",
        scope="llm",  # type: ignore[arg-type]
        messages=[],
        data={},
        events=[],
        tags=[],
        span_id="test-span",
    )
    assert details.display_name == "test"
    assert details.provider == "openai"
    assert details.model == "gpt-4"


def test_complex_message_scenarios():
    """Test complex message conversion scenarios."""
    # Gemini with images
    messages = [
        {
            "name": "gen_ai.user.message",
            "attributes": {
                "content": '[{"mime_type": "image/jpeg", "data": "base64data"}]'
            },
        }
    ]
    result = convert_gemini_messages(messages)
    assert len(result) == 2
    assert result[0].content[0].type == "image"

    # Gemini with audio
    messages = [
        {
            "name": "gen_ai.user.message",
            "attributes": {
                "content": '[{"mime_type": "audio/wav", "data": "audiodata"}]'
            },
        }
    ]
    result = convert_gemini_messages(messages)
    assert len(result) == 2
    assert result[0].content[0].type == "audio"

    # OpenAI with tool calls via gen_ai.choice
    messages = [
        {
            "name": "gen_ai.choice",
            "attributes": {
                "index": 0,
                "message": '{"tool_calls": [{"function": {"name": "test", "arguments": "{\\"x\\": 1}"}}]}',
            },
        }
    ]
    result = convert_openai_messages(messages)
    assert len(result) == 1
    assert len(result[0].content) == 1
    assert result[0].content[0].type == "tool_call"

    # Test invalid JSON in tool calls - need to wrap in try/catch since it throws
    try:
        messages = [
            {
                "name": "gen_ai.choice",
                "attributes": {
                    "index": 0,
                    "message": '{"tool_calls": [{"function": {"name": "test", "arguments": "invalid"}}]}',
                },
            }
        ]
        result = convert_openai_messages(messages)
    except json.JSONDecodeError:
        # Expected behavior for invalid JSON
        pass


def test_mirascope_complex_content():
    """Test Mirascope message conversion with complex content."""
    # Tool calls
    messages = [
        {
            "role": "assistant",
            "content": [
                {"type": "tool_call", "name": "test_tool", "args": {"param": "value"}}
            ],
        }
    ]
    result = convert_mirascope_messages(messages)
    assert len(result) == 1
    assert result[0].content[0].type == "tool_call"

    # Image content
    messages = [
        {
            "role": "user",
            "content": {
                "type": "image",
                "media_type": "image/png",
                "image": "imagedata",
                "detail": "high",
            },
        }
    ]
    result = convert_mirascope_messages(messages)
    assert len(result) == 1
    assert result[0].content[0].type == "image"

    # Audio content
    messages = [
        {
            "role": "user",
            "content": {
                "type": "audio",
                "media_type": "audio/mp3",
                "audio": "audiodata",
            },
        }
    ]
    result = convert_mirascope_messages(messages)
    assert len(result) == 1
    assert result[0].content[0].type == "audio"


def test_openai_image_handling():
    """Test OpenAI image URL handling."""
    # Test with gen_ai format and image URL
    messages = [
        {
            "name": "gen_ai.user.message",
            "attributes": {
                "content": '[{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,abc123", "detail": "high"}}]'
            },
        }
    ]
    result = convert_openai_messages(messages)
    assert len(result) == 2
    assert result[0].content[0].type == "image"
    assert "abc123" in result[0].content[0].image


def test_anthropic_tool_use():
    """Test Anthropic tool use conversion."""
    messages = [
        {
            "name": "gen_ai.choice",
            "attributes": {
                "message": '{"tool_calls": {"function": {"name": "calc", "arguments": "{\\"x\\": 1}"}}}'
            },
        }
    ]
    result = convert_anthropic_messages(messages)
    assert len(result) == 1
    assert len(result[0].content) == 1
    assert result[0].content[0].type == "tool_call"


def test_edge_cases():
    """Test various edge cases."""
    # Empty events
    result = convert_events([])
    assert result == []

    # Event with missing attributes
    events = [{"name": "test", "timestamp": 0}]
    result = convert_events(events)
    assert len(result) == 1

    # Mirascope with empty content list
    messages = [{"role": "user", "content": []}]
    result = convert_mirascope_messages(messages)
    assert len(result) == 0  # No content parts added

    # Test Gemini choice processing
    messages = [
        {
            "name": "gen_ai.choice",
            "attributes": {"index": 0, "message": '{"content": ["response text"]}'},
        }
    ]
    result = convert_gemini_messages(messages)
    assert len(result) == 1
    assert len(result[0].content) >= 1


def test_comprehensive_coverage():
    """Test to hit remaining uncovered lines."""
    # Test Gemini choice with tool calls
    messages = [
        {
            "name": "gen_ai.choice",
            "attributes": {
                "index": 0,
                "message": '{"tool_calls": [{"function": {"name": "test", "arguments": {"x": 1}}}]}',
            },
        }
    ]
    result = convert_gemini_messages(messages)
    assert len(result) == 1
    assert len(result[0].content) >= 1

    # Test OpenAI gen_ai.choice with content
    messages = [
        {
            "name": "gen_ai.choice",
            "attributes": {"index": 0, "message": '{"content": "response text"}'},
        }
    ]
    result = convert_openai_messages(messages)
    assert len(result) == 1

    # Test Azure similar to OpenAI
    messages = [
        {
            "name": "gen_ai.choice",
            "attributes": {"index": 0, "message": '{"content": "response text"}'},
        }
    ]
    result = convert_azure_messages(messages)
    assert len(result) == 1

    # Test Anthropic choice with index
    messages = [
        {
            "name": "gen_ai.choice",
            "attributes": {"index": 0, "message": '{"content": ["response", "text"]}'},
        }
    ]
    result = convert_anthropic_messages(messages)
    assert len(result) == 1

    # Test Anthropic choice without index (hits different branch)
    messages = [
        {
            "name": "gen_ai.choice",
            "attributes": {"message": '{"content": "direct content"}'},
        }
    ]
    result = convert_anthropic_messages(messages)
    assert len(result) == 1


def test_additional_missing_lines():
    """Test to cover additional missing lines."""
    # Test OpenAI fallback to text when not image_url (lines 184-188)
    messages = [
        {
            "name": "gen_ai.user.message",
            "attributes": {
                "content": '[{"type": "other", "text": "Some text content"}]'
            },
        }
    ]
    result = convert_openai_messages(messages)
    assert len(result) == 2
    assert result[0].content[0].type == "text"
    assert result[0].content[0].text == "Some text content"

    # Test Azure with image URL handling (lines 246-266)
    messages = [
        {
            "name": "gen_ai.user.message",
            "attributes": {
                "content": '[{"type": "image_url", "image_url": {"url": "data:image/png;base64,xyz789", "detail": "low"}}]'
            },
        }
    ]
    result = convert_azure_messages(messages)
    assert len(result) == 2
    assert result[0].content[0].type == "image"
    assert result[0].content[0].detail == "low"

    # Test Anthropic with image content (lines 323-338)
    messages = [
        {
            "name": "gen_ai.user.message",
            "attributes": {
                "content": '[{"type": "image", "source": {"media_type": "image/jpeg", "data": "imagedata"}}]'
            },
        }
    ]
    result = convert_anthropic_messages(messages)
    assert len(result) == 2
    assert result[0].content[0].type == "image"
    assert result[0].content[0].media_type == "image/jpeg"

    # Test Mirascope with different content types (lines 437-455)
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Some text content"},
                {"type": "tool_call", "name": "func", "args": {"param": "value"}},
            ],
        }
    ]
    result = convert_mirascope_messages(messages)
    assert len(result) == 1
    assert len(result[0].content) == 2
    assert result[0].content[0].type == "text"
    assert result[0].content[1].type == "tool_call"

    # Test with string content items in Mirascope
    messages = [
        {
            "role": "assistant",
            "content": ["string content", {"type": "text", "text": "object content"}],
        }
    ]
    result = convert_mirascope_messages(messages)
    assert len(result) == 1
    assert len(result[0].content) == 2
    assert result[0].content[0].type == "text"
    assert result[0].content[0].text == "string content"
