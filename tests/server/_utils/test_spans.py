# tests/server/_utils/test_spans.py

from lilypad.server._utils.spans import (
    convert_anthropic_messages,
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
    assert result[0].content[0].text == "Hello, how are you?"
    assert result[1].role == "assistant"
    assert result[1].content[0].text == "I am doing well, thank you!"


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
    assert result[0].content[0].text == "Test message"
    assert result[1].role == "assistant"
    assert result[1].content[0].text == "Response"


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
    assert result[0].content[0].text == "User input"
    assert result[1].role == "assistant"
    assert result[1].content[0].text == "Assistant response"


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
    assert result[0].content[0].text == "Invalid JSON"

    result = convert_anthropic_messages(messages)
    assert result[0].content[0].text == "Invalid JSON"

    result = convert_gemini_messages(messages)
    assert result[0].content[0].text == "Invalid JSON"
