# tests/server/_utils/test_spans.py

from lilypad.server._utils.spans import (
    convert_anthropic_messages,
    convert_events,
    convert_gemini_messages,
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
