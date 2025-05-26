"""Tests for the Message class"""

from abc import ABC
from typing import Any

import jiter
import pytest
from pydantic import computed_field
from mirascope.core import base as mb
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionMessageToolCall,
    ChatCompletionToolMessageParam,
)
from mirascope.core.base import _utils as mb_utils
from pydantic.json_schema import SkipJsonSchema
from mirascope.core.openai import OpenAICallParams
from mirascope.core.base.tool import BaseTool
from mirascope.core.base.types import CostMetadata
from mirascope.core.base.call_response import _BaseToolT
from openai.types.chat.chat_completion import Choice
from mirascope.core.openai.call_response import OpenAICallResponse

from lilypad.lib.messages import Message


class MockResponse(
    mb.BaseCallResponse[
        Any,
        mb.BaseTool,
        Any,
        mb.BaseDynamicConfig[Any, Any, Any],
        Any,
        mb.BaseCallParams,
        Any,
        mb_utils.BaseMessageParamConverter,
    ]
):
    """Mock response for testing"""

    _message_converter: type[mb_utils.BaseMessageParamConverter] = mb_utils.BaseMessageParamConverter

    @property
    def content(self) -> str:  # pyright: ignore [reportReturnType]
        """Returns the content of the response."""
        pass

    @property
    def finish_reasons(self) -> list[str] | None:
        """Returns the finish reasons of the response."""
        pass

    @property
    def model(self) -> str | None:
        """Returns the name of the response model."""
        pass

    @property
    def id(self) -> str | None:
        """Returns the id of the response."""
        pass

    @property
    def usage(self) -> Any:
        """Returns the usage of the chat completion."""
        pass

    @property
    def input_tokens(self) -> int | float | None:
        """Returns the number of input tokens."""
        pass

    @property
    def output_tokens(self) -> int | float | None:
        """Returns the number of output tokens."""
        pass

    @property
    def cached_tokens(self) -> int | None:
        """Returns the number of cached tokens."""
        pass

    @property
    def cost(self) -> float | None:
        """Returns the cost of the response in dollars."""
        pass

    @property
    def cost_metadata(self) -> CostMetadata:
        """Returns the cost of the response in dollars."""
        return CostMetadata(
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            cached_tokens=self.cached_tokens,
        )

    @property
    def message_param(self) -> Any:  # pyright: ignore [reportInvalidTypeVarUse, reportIncompatibleVariableOverride]
        """Returns the assistants's response as a message parameter."""
        pass

    @property
    def common_user_message_param(self) -> mb.BaseMessageParam | None:
        """Provider-agnostic user message param."""
        ...

    @computed_field
    @property
    def tools(self) -> list[BaseTool] | None:  # pyright: ignore [reportInvalidTypeVarUse, reportIncompatibleVariableOverride]
        """Returns any available tool calls as their `OpenAITool` definition.

        Raises:
            ValidationError: if a tool call doesn't match the tool's schema.
            ValueError: if the model refused to response, in which case the error
                message will be the refusal.
        """
        if hasattr(self.response.choices[0].message, "refusal") and (
            refusal := self.response.choices[0].message.refusal
        ):
            raise ValueError(refusal)

        tool_calls = self.response.choices[0].message.tool_calls
        if not self.tool_types or not tool_calls:
            return None

        extracted_tools = []
        for tool_call in tool_calls:
            for tool_type in self.tool_types:
                if tool_call.function.name == tool_type._name():
                    extracted_tools.append(tool_type.from_tool_call(tool_call))  # pyright: ignore [reportAttributeAccessIssue]
                    break

        return extracted_tools

    @property
    def tool(self) -> _BaseToolT | None:  # pyright: ignore [reportInvalidTypeVarUse, reportIncompatibleVariableOverride]
        """Returns the tool that was used to generate the response."""
        pass

    @classmethod
    def tool_message_params(  # pyright: ignore [reportIncompatibleMethodOverride]
        cls, tools_and_outputs: list[tuple[BaseTool, str]]
    ) -> list[ChatCompletionToolMessageParam]:
        """Returns the tool message parameters for tool call results.

        Args:
            tools_and_outputs: The list of tools and their outputs from which the tool
                message parameters should be constructed.

        Returns:
            The list of constructed `ChatCompletionToolMessageParam` parameters.
        """
        return [
            ChatCompletionToolMessageParam(  # pyright: ignore [reportCallIssue]
                role="tool",
                content=output,
                tool_call_id=tool.tool_call.id,  # pyright: ignore [reportAttributeAccessIssue]
                name=tool._name(),  # pyright: ignore [reportCallIssue]
            )
            for tool, output in tools_and_outputs
        ]

    @property
    def common_finish_reasons(self) -> list[mb.types.FinishReason] | None:
        """Provider-agnostic finish reasons."""
        ...

    @property
    def common_message_param(self) -> mb.BaseMessageParam:
        """Provider-agnostic assistant message param."""
        ...


class MockBaseTool(BaseTool, ABC):
    """Mock base tool for testing"""

    tool_call: SkipJsonSchema[ChatCompletionMessageToolCall]

    @classmethod
    def from_tool_call(cls, tool_call: ChatCompletionMessageToolCall) -> BaseTool:
        """Constructs an `OpenAITool` instance from a `tool_call`.

        Args:
            tool_call: The OpenAI tool call from which to construct this tool instance.
        """
        model_json = jiter.from_json(tool_call.function.arguments.encode())  # pyright: ignore [reportArgumentType]
        model_json["tool_call"] = tool_call.model_dump()
        return cls.model_validate(model_json)


class FormatBook(MockBaseTool):
    """Mock tool that formats the book"""

    title: str
    author: str

    def call(self) -> str:
        """Return the formatted book"""
        return f"{self.title} by {self.author}"


class FormatAuthor(MockBaseTool):
    """Mock tool that formats the author"""

    author: str

    def call(self) -> str:
        """Return the author"""
        return f"Author is {self.author}"


class MockAsyncTool(BaseTool):
    """Mock async tool for testing"""

    value: str

    async def call(self) -> str:
        """Return the value"""
        return self.value


class ErrorTool(BaseTool):
    """Mock tool that raises an error"""

    async def call(self) -> str:
        """Raise an error"""
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
                ),
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
    message = Message(mock_openai_response)  # pyright: ignore [reportAbstractUsage]
    assert message.content == "test content"
    assert message._response == mock_openai_response


def test_message_attribute_delegation(mock_openai_response):
    """Test attribute delegation to wrapped response"""
    message = Message(mock_openai_response)  # pyright: ignore [reportAbstractUsage]
    assert message.content == mock_openai_response.content
    assert message.model == mock_openai_response.model
    assert message.id == mock_openai_response.id


def test_message_special_attributes(mock_openai_response):
    """Test access to special attributes"""
    message = Message(mock_openai_response)  # pyright: ignore [reportAbstractUsage]
    assert isinstance(message.model_fields, dict)
    assert isinstance(message.__dict__, dict)
    assert isinstance(message.__class__, type)


#
# def test_message_no_tools(mock_openai_response):
#     """Test call_tools with no tools"""
#     message = Message(mock_openai_response)  # pyright: ignore [reportAbstractUsage]
#     result = message.call_tools()
#     assert isinstance(result, list)
#     assert len(result) == 0
#

# def test_message_sync_tools(mock_chat_completion):
#     """Test call_tools with synchronous tools"""
#     mock_chat_completion.choices[0].message.tool_calls = [
#         ChatCompletionMessageToolCall(
#             id="tool1-id",
#             type="function",
#             function=Function(
#                 name="FormatBook",
#                 arguments='{"title": "The Name of the Wind", "author": "Patrick Rothfuss"}',
#             ),
#         ),
#         ChatCompletionMessageToolCall(
#             id="tool2-id",
#             type="function",
#             function=Function(
#                 name="FormatAuthor", arguments='{"author": "Patrick Rothfuss"}'
#             ),
#         ),
#     ]
#
#     response = MockResponse(  # pyright: ignore [reportAbstractUsage]
#         metadata={},
#         response=mock_chat_completion,
#         tool_types=[FormatBook, FormatAuthor],
#         prompt_template=None,
#         fn_args={},
#         dynamic_config=None,
#         messages=[],
#         call_params=OpenAICallParams(),
#         call_kwargs={},
#         user_message_param=None,
#         start_time=0.0,
#         end_time=0.0,
#     )
#
#     message = Message[FormatBook, FormatAuthor](response)  # pyright: ignore [reportAbstractUsage]
#     result = message.call_tools()
#     assert isinstance(result, list)
#     assert len(result) == 2
#     assert result[0]["tool_call_id"] == "tool1-id"
#     assert result[0]["content"] == "The Name of the Wind by Patrick Rothfuss"
#     assert result[1]["tool_call_id"] == "tool2-id"
#     assert result[1]["content"] == "Author is Patrick Rothfuss"


# @pytest.mark.asyncio
# async def test_message_async_tools(mock_chat_completion):
#     """Test call_tools with asynchronous tools"""
#
#     async def async_call() -> str:
#         return "async result"
#
#     class AsyncFormatBook(MockBaseTool):
#         title: str
#         author: str
#
#         async def call(self) -> str:
#             return f"{self.title} by {self.author} (async)"
#
#     class AsyncFormatAuthor(MockBaseTool):
#         author: str
#
#         async def call(self) -> str:
#             return f"Author is {self.author} (async)"
#
#     mock_chat_completion.choices[0].message.tool_calls = [
#         ChatCompletionMessageToolCall(
#             id="tool1-id",
#             type="function",
#             function=Function(
#                 name="AsyncFormatBook",
#                 arguments='{"title": "The Name of the Wind", "author": "Patrick Rothfuss"}',
#             ),
#         ),
#         ChatCompletionMessageToolCall(
#             id="tool2-id",
#             type="function",
#             function=Function(
#                 name="AsyncFormatAuthor", arguments='{"author": "Patrick Rothfuss"}'
#             ),
#         ),
#     ]
#
#     response = MockResponse(  # pyright: ignore [reportAbstractUsage]
#         metadata={},
#         response=mock_chat_completion,
#         tool_types=[AsyncFormatBook, AsyncFormatAuthor],
#         prompt_template=None,
#         fn_args={},
#         dynamic_config=None,
#         messages=[],
#         call_params=OpenAICallParams(),
#         call_kwargs={},
#         user_message_param=None,
#         start_time=0.0,
#         end_time=0.0,
#     )
#
#     message = Message(response)  # pyright: ignore [reportAbstractUsage]
#     results = await message.call_tools()  # pyright: ignore [reportAbstractUsage, reportGeneralTypeIssues]
#
#     assert isinstance(results, list)
#     assert len(results) == 2
#
#     tool1, output1 = results[0]
#     tool2, output2 = results[1]
#
#     assert isinstance(tool1, AsyncFormatBook)
#     assert isinstance(tool2, AsyncFormatAuthor)
#     assert output1 == "The Name of the Wind by Patrick Rothfuss (async)"
#     assert output2 == "Author is Patrick Rothfuss (async)"


# @pytest.mark.asyncio
# async def test_message_tool_error_handling(mock_chat_completion):
#     """Test error handling in tool calls"""
#
#     class AsyncErrorTool(MockBaseTool):
#         async def call(self) -> str:
#             raise ValueError("Async tool error")
#
#     mock_chat_completion.choices[0].message.tool_calls = [
#         ChatCompletionMessageToolCall(
#             id="error-tool-id",
#             type="function",
#             function=Function(name="AsyncErrorTool", arguments="{}"),
#         )
#     ]
#
#     response = MockResponse(  # pyright: ignore [reportAbstractUsage]
#         metadata={},
#         response=mock_chat_completion,
#         tool_types=[AsyncErrorTool],
#         prompt_template=None,
#         fn_args={},
#         dynamic_config=None,
#         messages=[],
#         call_params=OpenAICallParams(),
#         call_kwargs={},
#         user_message_param=None,
#         start_time=0.0,
#         end_time=0.0,
#     )
#
#     message = Message[AsyncErrorTool](response)  # pyright: ignore [reportAbstractUsage]
#     with pytest.raises(ValueError, match="Async tool error"):
#         await message.call_tools()  # pyright: ignore [reportGeneralTypeIssues]
