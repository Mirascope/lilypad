"""Test cases for the spans schema."""

import base64
import json

from lilypad.server.schemas.span_more_details import (
    convert_anthropic_messages,
    convert_azure_messages,
    convert_events,
    convert_gemini_messages,
    convert_mirascope_messages,
    convert_openai_messages,
)


def test_convert_openai_messages():
    """Test converting OpenAI messages"""
    messages = [
        {
            "name": "gen_ai.user.message",
            "attributes": {"content": '["Hello, how are you?"]'},
        },
        {
            "name": "gen_ai.choice",
            "attributes": {
                "index": 0,
                "message": '{"role": "assistant", "content": "I am doing well, thank you!"}',
            },
        },
    ]

    result = convert_openai_messages(messages)
    assert len(result) == 2
    assert result[0].role == "user"
    assert result[0].content[0].text == "Hello, how are you?"  # pyright: ignore [reportAttributeAccessIssue]
    assert result[1].role == "assistant"
    assert result[1].content[0].text == "I am doing well, thank you!"  # pyright: ignore [reportAttributeAccessIssue]


def test_convert_gemini_messages():
    """Test converting Gemini messages"""
    messages = [
        {"name": "gen_ai.user.message", "attributes": {"content": '["Test message"]'}},
        {
            "name": "gen_ai.choice",
            "attributes": {
                "index": 0,
                "message": '{"role": "assistant", "content": ["Response"]}',
            },
        },
    ]

    result = convert_gemini_messages(messages)
    assert len(result) == 2
    assert result[0].role == "user"
    assert result[0].content[0].text == "Test message"  # pyright: ignore [reportAttributeAccessIssue]
    assert result[1].role == "assistant"
    assert result[1].content[0].text == "Response"  # pyright: ignore [reportAttributeAccessIssue]


def test_convert_anthropic_messages():
    """Test converting Anthropic messages"""
    messages = [
        {"name": "gen_ai.user.message", "attributes": {"content": '["User input"]'}},
        {
            "name": "gen_ai.choice",
            "attributes": {
                "index": 0,
                "message": '{"role": "assistant", "content": "Assistant response"}',
            },
        },
    ]

    result = convert_anthropic_messages(messages)
    assert len(result) == 2
    assert result[0].role == "user"
    assert result[0].content[0].text == "User input"  # pyright: ignore [reportAttributeAccessIssue]
    assert result[1].role == "assistant"
    assert result[1].content[0].text == "Assistant response"  # pyright: ignore [reportAttributeAccessIssue]


def test_convert_azure_messages():
    """Test converting Azure messages"""
    messages = [
        {
            "name": "gen_ai.user.message",
            "gen_ai.system": "az.ai.inference",
            "attributes": {"content": "Hello, how are you?"},
        },
        {
            "name": "gen_ai.choice",
            "attributes": {
                "index": 0,
                "message": '{"role": "assistant", "content": "I am doing well, thank you!"}',
                "finish_reason": "stop",
            },
        },
    ]

    result = convert_azure_messages(messages)
    assert len(result) == 2
    assert result[0].role == "user"
    assert result[0].content[0].text == "Hello, how are you?"  # pyright: ignore [reportAttributeAccessIssue]
    assert result[1].role == "assistant"
    assert result[1].content[0].text == "I am doing well, thank you!"  # pyright: ignore [reportAttributeAccessIssue]


def test_invalid_message_content():
    """Test handling invalid message content."""
    messages = [
        {"name": "gen_ai.user.message", "attributes": {"content": "Invalid JSON"}},
        {
            "name": "gen_ai.choice",
            "attributes": {
                "index": 0,
                "message": '{"role": "assistant", "content": "Response"}',
            },
        },
    ]

    result = convert_openai_messages(messages)
    assert result[0].content[0].text == "Invalid JSON"  # pyright: ignore [reportAttributeAccessIssue]

    result = convert_anthropic_messages(messages)
    assert result[0].content[0].text == "Invalid JSON"  # pyright: ignore [reportAttributeAccessIssue]

    result = convert_gemini_messages(messages)
    assert result[0].content[0].text == "Invalid JSON"  # pyright: ignore [reportAttributeAccessIssue]


def test_convert_events():
    """Test converting events."""
    events = [
        {
            "name": "event1",
            "attributes": {"event1.type": "value1"},
        },
        {
            "name": "event2",
            "attributes": {"event2.message": "value2"},
        },
    ]
    results = convert_events(events)
    assert results[0].type == "value1"
    assert results[0].name == "event1"
    assert results[1].message == "value2"
    assert results[1].name == "event2"


def test_convert_mirascope_image_message():
    """Test converting Mirascope message."""
    import base64

    # Your mock image bytes
    mock_image_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00"

    encoded_image = base64.b64encode(mock_image_bytes).decode("utf-8")

    mock_message = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "I need to extract information.",
                },
                {"type": "image", "media_type": "image/jpeg", "image": encoded_image},
            ],
        }
    ]
    mock_message_string = json.dumps(mock_message)

    results = convert_mirascope_messages(mock_message_string)
    assert results[0].role == "user"
    assert results[0].content[0].type == "text"
    assert results[0].content[0].text == "I need to extract information."
    assert results[0].content[1].type == "image"
    assert results[0].content[1].media_type == "image/jpeg"
    assert results[0].content[1].image == "/9j/4AAQSkZJRgABAQEASABIAAA="
    assert results[0].content[1].detail is None


def test_convert_mirascope_dict_audio_content():
    """Test converting message with dict-style audio content."""
    mock_audio_bytes = b"\xff\xfb\x90\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    encoded_audio = base64.b64encode(mock_audio_bytes).decode("utf-8")

    mock_message = [
        {
            "role": "user",
            "content": {
                "type": "audio",
                "media_type": "audio/wav",
                "audio": encoded_audio,
            },
        }
    ]
    mock_message_string = json.dumps(mock_message)

    results = convert_mirascope_messages(mock_message_string)
    assert len(results) == 1
    assert results[0].role == "user"
    assert results[0].content[0].type == "audio"
    assert results[0].content[0].media_type == "audio/wav"
