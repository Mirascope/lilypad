from types import GenericAlias

import pytest
from mirascope.core import base as mb
from mirascope.core.openai.call_response import OpenAICallResponse
from mirascope.core.openai.tool import OpenAITool
from mirascope.core.openai import OpenAICallParams
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionMessageToolCall,
)
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message_tool_call import Function

from lilypad.messages import Message


class FormatBook(OpenAITool):
    title: str
    author: str

    def call(self) -> str:
        return f"{self.title} by {self.author}"


class MockAsyncTool(OpenAITool):
    """Mock async tool for testing"""
    value: str

    async def call(self) -> str:
        return self.value

class ErrorTool(OpenAITool):
    async def call(self) -> str:
        raise ValueError("Tool error")

@pytest.fixture
def mock_chat_completion() -> ChatCompletion:
    """Create a mock ChatCompletion"""
    return ChatCompletion(
        id="test-id",
        choices=[
            Choice(
                finish_reason="stop",
                index=0,
                message=ChatCompletionMessage(
                    content="test content",
                    role="assistant",
                )
            )
        ],
        created=0,
        model="gpt-4",
        object="chat.completion",
        system_fingerprint="test-fingerprint",
    )

@pytest.fixture
def mock_openai_response(mock_chat_completion) -> OpenAICallResponse:
    """Create a mock OpenAICallResponse"""
    return OpenAICallResponse(
        metadata={},
        response=mock_chat_completion,
        tool_types=None,
        prompt_template=None,
        fn_args={},
        dynamic_config=None,
        messages=[],
        call_params=OpenAICallParams(),
        call_kwargs={},
        user_message_param=None,
        start_time=0.0,
        end_time=0.0,
    )

def test_message_initialization(mock_openai_response):
    """Test Message class initialization"""
    message = Message(mock_openai_response)
    assert message.content == "test content"
    assert message._response == mock_openai_response

def test_message_attribute_delegation(mock_openai_response):
    """Test attribute delegation to wrapped response"""
    message = Message(mock_openai_response)
    assert message.content == mock_openai_response.content
    assert message.model == mock_openai_response.model
    assert message.id == mock_openai_response.id

def test_message_special_attributes(mock_openai_response):
    """Test access to special attributes"""
    message = Message(mock_openai_response)
    assert isinstance(message.model_fields, dict)
    assert isinstance(message.__dict__, dict)
    assert isinstance(message.__class__, type)

def test_message_no_tools(mock_openai_response):
    """Test call_tools with no tools"""
    message = Message(mock_openai_response)
    result = message.call_tools()
    assert isinstance(result, list)
    assert len(result) == 0

def test_message_sync_tools(mock_chat_completion):
    """Test call_tools with synchronous tools"""
    mock_chat_completion.choices[0].message.tool_calls = [
        ChatCompletionMessageToolCall(
            id="tool1-id",
            type="function",
            function=Function(name="MockTool", arguments='{"value": "tool1"}')
        ),
        ChatCompletionMessageToolCall(
            id="tool2-id",
            type="function",
            function=Function(name="MockTool", arguments='{"value": "tool2"}')
        )
    ]

    response = OpenAICallResponse(
        metadata={},
        response=mock_chat_completion,
        tool_types=[FormatBook],
        prompt_template=None,
        fn_args={},
        dynamic_config=None,
        messages=[],
        call_params=OpenAICallParams(),
        call_kwargs={},
        user_message_param=None,
        start_time=0.0,
        end_time=0.0,
    )

    message = Message[FormatBook](response)
    result = message.call_tools()
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(item, tuple) for item in result)
    assert result[0][1] == "tool1"
    assert result[1][1] == "tool2"
