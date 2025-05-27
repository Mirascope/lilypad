"""Shared test fixtures and mocks."""

from typing import Any, Generic, TypeVar
from unittest.mock import Mock

import pytest
from jiter import jiter  # pyright: ignore [reportAttributeAccessIssue]
from pydantic import BaseModel, computed_field
from mirascope import Provider
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionMessageToolCall,
    ChatCompletionToolMessageParam,
)
from mirascope.core.base import BaseTool
from pydantic.json_schema import SkipJsonSchema
from openai.types.chat.chat_completion import Choice

# Type variable for generic tool type
T = TypeVar("T")


@pytest.fixture
def test_response_model():
    """Create a TestResponseModel class for testing."""

    class TestResponseModel(BaseModel):
        """Test response model for testing."""

        message: str

    return TestResponseModel


@pytest.fixture
def mock_chat_completion() -> ChatCompletion:
    """Create a mock ChatCompletion for testing."""
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
def mock_response():
    """Creates a base MockResponse class for testing.
    This is used across multiple test files to ensure consistency in mocking responses.
    """

    class MockResponse(BaseModel):
        metadata: dict
        response: Any
        tool_types: list[type[BaseTool]] | None
        prompt_template: str | None
        fn_args: dict
        dynamic_config: Any
        messages: list
        call_params: dict
        call_kwargs: dict
        start_time: int | float
        end_time: int | float

        @property
        def content(self) -> str:
            return self.response.choices[0].message.content

        @property
        def finish_reasons(self) -> list[str] | None:
            return [choice.finish_reason for choice in self.response.choices]

        @property
        def model(self) -> str | None:
            return self.response.model

        @property
        def id(self) -> str | None:
            return self.response.id

        @property
        def usage(self) -> Any:
            return self.response.usage

        @property
        def input_tokens(self) -> int | float | None:
            return None

        @property
        def output_tokens(self) -> int | float | None:
            return None

        @property
        def cost(self) -> float | None:
            return None

        @property
        def message_param(self) -> Any:
            return None

        @computed_field
        @property
        def tools(self) -> list[BaseTool] | None:
            if hasattr(self.response.choices[0].message, "refusal") and (
                refusal := self.response.choices[0].message.refusal
            ):
                raise ValueError(refusal)

            tool_calls = getattr(self.response.choices[0].message, "tool_calls", None)
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
        def tool(self) -> BaseTool | None:
            return None

        @classmethod
        def tool_message_params(
            cls, tools_and_outputs: list[tuple[BaseTool, str]]
        ) -> list[ChatCompletionToolMessageParam]:
            return [
                ChatCompletionToolMessageParam(  # pyright: ignore [reportCallIssue]
                    role="tool",
                    content=output,
                    tool_call_id=tool.tool_call.id,  # pyright: ignore [reportAttributeAccessIssue]
                    name=tool._name(),
                )
                for tool, output in tools_and_outputs
            ]

    return MockResponse


@pytest.fixture
def mock_base_tool():
    """Creates a base MockBaseTool class for testing.
    Used as a parent class for specific tool implementations in tests.
    """

    class MockBaseTool(BaseTool, Generic[T]):
        tool_call: SkipJsonSchema[ChatCompletionMessageToolCall]

        @classmethod
        def from_tool_call(cls, tool_call: ChatCompletionMessageToolCall) -> "MockBaseTool":
            model_json = jiter.from_json(tool_call.function.arguments.encode())
            model_json["tool_call"] = tool_call.model_dump()
            return cls.model_validate(model_json)

    return MockBaseTool


@pytest.fixture
def format_book(mock_base_tool):
    """Create a FormatBook tool for testing."""

    class FormatBook(mock_base_tool):
        title: str
        author: str

        def call(self) -> str:
            return f"{self.title} by {self.author}"

    return FormatBook


@pytest.fixture
def format_author(mock_base_tool):
    """Create a FormatAuthor tool for testing."""

    class FormatAuthor(mock_base_tool):
        author: str

        def call(self) -> str:
            return f"Author is {self.author}"

    return FormatAuthor


@pytest.fixture
def create_mock_prompt():
    """Create a helper function for generating mock prompts."""

    def _create_mock_prompt():
        """Helper function to create a consistent mock prompt."""
        from unittest.mock import Mock

        mock_prompt = Mock()
        mock_prompt.provider = Mock()
        mock_prompt.provider.value = "openai"
        mock_prompt.template = "test template"
        mock_prompt.model = "test_model"
        mock_prompt.call_params = None
        return mock_prompt

    return _create_mock_prompt


@pytest.fixture
def mock_gemini_prompt(create_mock_prompt):
    """Create a mock prompt with Gemini provider settings."""
    mock_prompt = create_mock_prompt()
    mock_prompt.provider = Provider.GEMINI
    mock_prompt.call_params = Mock()
    mock_prompt.call_params.model_dump.return_value = {"test": "config"}
    return mock_prompt
