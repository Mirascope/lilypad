import json
import pytest

from lilypad._utils.spans import (
    MessageParam,
    _TextPart,
    _ImagePart,
    _AudioPart,
    group_span_keys,
    convert_gemini_messages,
    convert_anthropic_messages,
)


def test_message_param_base():
    # Test basic text message
    message = MessageParam(
        role="user",
        content=[_TextPart(type="text", text="Hello")]
    )
    assert message.role == "user"
    assert len(message.content) == 1
    assert message.content[0].text == "Hello"


def test_group_span_keys_basic():
    attributes = {
        "gen_ai.prompt.0.content": "Hello",
        "gen_ai.completion.0.content": "Hi there",
    }
    grouped = group_span_keys(attributes)
    assert "prompt.0" in grouped
    assert "completion.0" in grouped
    assert grouped["prompt.0"]["content"] == "Hello"
    assert grouped["completion.0"]["content"] == "Hi there"


def test_group_span_keys_with_tool_calls():
    attributes = {
        "gen_ai.completion.0.tool_calls.0.name": "search",
        "gen_ai.completion.0.tool_calls.0.arguments": '{"query": "test"}'
    }
    grouped = group_span_keys(attributes)
    assert "completion.0" in grouped
    assert len(grouped["completion.0"]["tool_calls"]) == 1
    assert grouped["completion.0"]["tool_calls"][0]["name"] == "search"
    assert grouped["completion.0"]["tool_calls"][0]["arguments"] == {"query": "test"}


def test_group_span_keys_invalid_arguments():
    attributes = {
        "gen_ai.completion.0.tool_calls.0.arguments": 'invalid json',
        "gen_ai.completion.0.tool_calls.0.name": "search"
    }
    grouped = group_span_keys(attributes)
    assert grouped["completion.0"]["tool_calls"][0]["arguments"] == "invalid json"


def test_group_span_keys_ignores_non_genai():
    attributes = {
        "gen_ai.prompt.0.content": "Hello",
        "other.key": "value"
    }
    grouped = group_span_keys(attributes)
    assert len(grouped) == 1
    assert "prompt.0" in grouped
    assert grouped["prompt.0"]["content"] == "Hello"


def test_group_span_keys_multiple_tool_calls():
    attributes = {
        "gen_ai.completion.0.tool_calls.0.name": "search1",
        "gen_ai.completion.0.tool_calls.1.name": "search2"
    }
    grouped = group_span_keys(attributes)
    assert len(grouped["completion.0"]["tool_calls"]) == 2


def test_convert_gemini_messages_text():
    messages = {
        "prompt.0": {
            "user": json.dumps(["Hello"])
        },
        "completion.0": {
            "content": "Hi there"
        }
    }
    result = convert_gemini_messages(messages)
    assert len(result) == 2
    assert result[0].role == "user"
    assert isinstance(result[0].content[0], _TextPart)
    assert result[0].content[0].text == "Hello"
    assert result[1].role == "assistant"
    assert result[1].content[0].text == "Hi there"


def test_convert_gemini_messages_with_image():
    messages = {
        "prompt.0": {
            "user": json.dumps([{
                "mime_type": "image/jpeg",
                "data": "base64data"
            }])
        }
    }
    result = convert_gemini_messages(messages)
    assert len(result) == 1
    assert isinstance(result[0].content[0], _ImagePart)
    assert result[0].content[0].media_type == "image/jpeg"
    assert result[0].content[0].image == "base64data"


def test_convert_gemini_messages_with_audio():
    messages = {
        "prompt.0": {
            "user": json.dumps([{
                "mime_type": "audio/wav",
                "data": "base64audio"
            }])
        }
    }
    result = convert_gemini_messages(messages)
    assert len(result) == 1
    assert isinstance(result[0].content[0], _AudioPart)
    assert result[0].content[0].media_type == "audio/wav"
    assert result[0].content[0].audio == "base64audio"


def test_convert_anthropic_messages_basic():
    messages = {
        "prompt.0": {
            "content": "Hello"
        },
        "completion.0": {
            "content": "Hi there"
        }
    }
    result = convert_anthropic_messages(messages)
    assert len(result) == 2
    assert result[0].role == "user"
    assert result[0].content[0].text == "Hello"
    assert result[1].role == "assistant"
    assert result[1].content[0].text == "Hi there"


def test_convert_anthropic_messages_with_json_content():
    messages = {
        "prompt.0": {
            "content": json.dumps([
                {"type": "text", "text": "Hello"},
                {"type": "image", "source": {"media_type": "image/jpeg", "data": "base64img"}}
            ])
        }
    }
    result = convert_anthropic_messages(messages)
    assert len(result) == 1
    assert len(result[0].content) == 2
    assert isinstance(result[0].content[0], _TextPart)
    assert isinstance(result[0].content[1], _ImagePart)


def test_convert_anthropic_messages_completion_dict():
    messages = {
        "completion.0": {
            "content": {"text": "Hello"}
        }
    }
    result = convert_anthropic_messages(messages)
    assert len(result) == 1
    assert result[0].content[0].text == "Hello"


def test_convert_anthropic_messages_with_tool_calls():
    messages = {
        "completion.0": {
            "content": "Hello",
            "tool_calls": [{"name": "search"}]
        }
    }
    result = convert_anthropic_messages(messages)
    assert len(result) == 1
    assert result[0].content[0].text == "Hello"


def test_convert_anthropic_messages_empty_content():
    messages = {
        "completion.0": {
            "content": None
        }
    }
    result = convert_anthropic_messages(messages)
    assert len(result) == 0


def test_convert_anthropic_messages_invalid_json_content():
    messages = {
        "prompt.0": {
            "content": "invalid json {}"
        }
    }
    result = convert_anthropic_messages(messages)
    assert len(result) == 1
    assert result[0].content[0].text == "invalid json {}"


def test_group_span_keys_invalid_format():
    # Test handling of keys with insufficient parts
    attributes = {
        "gen_ai.invalid": "value",
        "gen_ai.prompt": "value"
    }
    grouped = group_span_keys(attributes)
    assert len(grouped) == 0

def test_group_span_keys_invalid_category():
    # Test handling of invalid categories
    attributes = {
        "gen_ai.prompt.0.content": "Hello",
        "gen_ai.invalid_category.0.content": "Should be ignored",
        "gen_ai.completion.0.content": "Hi there"
    }
    grouped = group_span_keys(attributes)
    assert len(grouped) == 2  # Only prompt and completion should be included
    assert "prompt.0" in grouped
    assert "completion.0" in grouped
    assert "invalid_category.0" not in grouped

def test_group_span_keys_all_invalid_categories():
    # Test when all categories are invalid
    attributes = {
        "gen_ai.unknown.0.content": "Will be ignored",
        "gen_ai.invalid.1.content": "Also ignored",
    }
    grouped = group_span_keys(attributes)
    assert len(grouped) == 0  # No valid categories, should return empty dict

def test_group_span_keys_mixed_categories():
    # Test mix of valid and invalid categories with various fields
    attributes = {
        "gen_ai.prompt.0.content": "Valid prompt",
        "gen_ai.invalid.0.content": "Invalid category",
        "gen_ai.completion.0.tool_calls.0.name": "search",
        "gen_ai.unknown.0.field": "Should be ignored",
        "gen_ai.test.0.content": "Another invalid category"
    }
    grouped = group_span_keys(attributes)
    assert len(grouped) == 2  # Only prompt and completion should be included
    assert "prompt.0" in grouped
    assert "completion.0" in grouped
    assert grouped["prompt.0"]["content"] == "Valid prompt"
    assert "tool_calls" in grouped["completion.0"]


def test_convert_anthropic_messages_string_parts():
    messages = {
        "prompt.0": {
            "content": json.dumps([
                "Plain text message",  # String part
                {"type": "text", "text": "Structured text"},  # Dict part
                "Another plain text"  # Another string part
            ])
        }
    }
    result = convert_anthropic_messages(messages)
    assert len(result) == 1
    assert len(result[0].content) == 3

    # Verify first string part was converted correctly
    assert isinstance(result[0].content[0], _TextPart)
    assert result[0].content[0].text == "Plain text message"

    # Verify dict part was handled correctly
    assert isinstance(result[0].content[1], _TextPart)
    assert result[0].content[1].text == "Structured text"

    # Verify second string part was converted correctly
    assert isinstance(result[0].content[2], _TextPart)
    assert result[0].content[2].text == "Another plain text"


def test_convert_anthropic_messages_mixed_content():
    messages = {
        "prompt.0": {
            "content": json.dumps([
                "Text message",  # String part
                {"type": "image", "source": {"media_type": "image/jpeg", "data": "base64img"}},  # Image part
                "More text",  # Another string part
                {"type": "text", "text": "Structured message"}  # Text dict part
            ])
        }
    }
    result = convert_anthropic_messages(messages)
    assert len(result) == 1
    assert len(result[0].content) == 4

    # Check string part
    assert isinstance(result[0].content[0], _TextPart)
    assert result[0].content[0].text == "Text message"

    # Check image part
    assert isinstance(result[0].content[1], _ImagePart)
    assert result[0].content[1].media_type == "image/jpeg"
    assert result[0].content[1].image == "base64img"

    # Check second string part
    assert isinstance(result[0].content[2], _TextPart)
    assert result[0].content[2].text == "More text"

    # Check structured text part
    assert isinstance(result[0].content[3], _TextPart)
    assert result[0].content[3].text == "Structured message"