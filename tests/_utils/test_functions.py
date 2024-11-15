"""Tests for lilypad._utils.functions module."""

import os
from abc import ABC
from collections.abc import AsyncIterable, Callable, Iterable
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from jiter import jiter  # pyright: ignore [reportAttributeAccessIssue]
from mirascope.core import base as mb
from mirascope.core.base.call_response import _BaseToolT
from mirascope.core.base.tool import BaseTool
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionMessageToolCall,
    ChatCompletionToolMessageParam,
)
from openai.types.chat.chat_completion import Choice
from pydantic import BaseModel, computed_field
from pydantic.json_schema import SkipJsonSchema

from lilypad import Message
from lilypad._utils.functions import create_mirascope_call, inspect_arguments
from lilypad.server.models import Provider


class MockResponse(
    mb.BaseCallResponse[
        Any,
        mb.BaseTool[Any],
        Any,
        mb.BaseDynamicConfig[Any, Any],
        Any,
        mb.BaseCallParams,
        Any,
    ]
):
    """Mock response for testing"""

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
    def cost(self) -> float | None:
        """Returns the cost of the response in dollars."""
        pass

    @property
    def message_param(self) -> Any:
        """Returns the assistants's response as a message parameter."""
        pass

    @computed_field
    @property
    def tools(self) -> list[BaseTool[Any]] | None:
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
    def tool(self) -> _BaseToolT | None:  # pyright: ignore [reportInvalidTypeVarUse]
        """Returns the tool that was used to generate the response."""
        pass

    @classmethod
    def tool_message_params(
        cls, tools_and_outputs: list[tuple[BaseTool[Any], str]]
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

    ...


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


class MockBaseTool(BaseTool[Any], ABC):
    """Mock base tool for testing"""

    tool_call: SkipJsonSchema[ChatCompletionMessageToolCall]

    @classmethod
    def from_tool_call(cls, tool_call: ChatCompletionMessageToolCall) -> BaseTool[Any]:
        """Constructs an `OpenAITool` instance from a `tool_call`.

        Args:
            tool_call: The OpenAI tool call from which to construct this tool instance.
        """
        model_json = jiter.from_json(tool_call.function.arguments.encode())
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


class MockAsyncTool(BaseTool[Any]):
    """Mock async tool for testing"""

    value: str

    async def call(self) -> str:
        """Return the value"""
        return self.value


class ErrorTool(BaseTool[Any]):
    """Mock tool that raises an error"""

    async def call(self) -> str:
        """Raise an error"""
        raise ValueError("Tool error")


def test_inspect_arguments_basic():
    """Test inspecting a basic function's arguments."""

    def test_func(x: int, y: str): ...

    arg_types, arg_values = inspect_arguments(test_func, 42, "hello")
    assert arg_types == {"x": "int", "y": "str"}
    assert arg_values == {"x": 42, "y": "hello"}


def test_inspect_arguments_with_defaults():
    """Test inspecting function with default values."""

    def test_func(x: int = 10, y: str = "default"): ...

    arg_types, arg_values = inspect_arguments(test_func)
    assert arg_types == {"x": "int", "y": "str"}
    assert arg_values == {"x": 10, "y": "default"}


def test_inspect_arguments_kwargs():
    """Test inspecting function with kwargs."""

    def test_func(**kwargs: dict[str, Any]): ...

    arg_types, arg_values = inspect_arguments(test_func, test=123)  # pyright: ignore [reportArgumentType]
    assert arg_types == {"kwargs": "dict[str, Any]"}
    assert arg_values == {"kwargs": {"test": 123}}


def test_inspect_arguments_complex_types():
    """Test inspecting function with complex type annotations."""

    def test_func(x: list[int], y: dict[str, Any]): ...

    arg_types, arg_values = inspect_arguments(test_func, [1, 2, 3], {"key": "value"})
    assert arg_types == {"x": "list[int]", "y": "dict[str, Any]"}
    assert arg_values == {"x": [1, 2, 3], "y": {"key": "value"}}


def test_inspect_arguments_no_annotations():
    """Test inspecting function without type annotations."""

    def test_func(x, y): ...

    arg_types, arg_values = inspect_arguments(test_func, 42, "hello")
    assert arg_types == {"x": "int", "y": "str"}
    assert arg_values == {"x": 42, "y": "hello"}


class TestResponseModel(BaseModel):
    """Mock response model for testing"""

    message: str


class CustomMessage(Message):
    """Custom message class for testing"""


async def async_test_fn(text: str) -> TestResponseModel:  # pyright: ignore [reportReturnType]
    """Mock async_test_fn function for testing."""


def sync_test_fn(text: str) -> TestResponseModel:  # pyright: ignore [reportReturnType]
    """Mock sync_test_fn function for testing."""


async def async_stream_test_fn(text: str) -> AsyncIterable[str]:  # pyright: ignore [reportReturnType]
    """Mock async_stream_test_fn function for testing."""


def sync_stream_test_fn(text: str) -> Iterable[str]:  # pyright: ignore [reportReturnType]
    """Mock sync_stream_test_fn function for testing."""


async def async_message_test_fn(text: str) -> Message[FormatBook]:  # pyright: ignore [reportReturnType]
    """Mock sync_stream_test_fn function for testing."""


def sync_message_test_fn(text: str) -> Message[FormatBook]:  # pyright: ignore [reportReturnType]
    """Mock sync_stream_test_fn function for testing."""


async def async_iterable_model_test_fn(text: str) -> Iterable[TestResponseModel]:  # pyright: ignore [reportReturnType]
    """Mock sync_stream_test_fn function for testing."""


def sync_iterable_model_test_fn(text: str) -> Iterable[TestResponseModel]:  # pyright: ignore [reportReturnType]
    """Mock function for testing."""


@pytest.fixture
def mock_prompt():
    """Mock for prompt with provider attribute."""
    prompt = Mock()
    prompt.provider = Mock()
    prompt.provider.value = "openai"
    prompt.template = "test template"
    prompt.model = "test_model"
    prompt.call_params = None
    return prompt


@pytest.fixture
def mock_gemini_prompt(mock_prompt):
    """Mock for Gemini prompt."""
    mock_prompt.provider = Provider.GEMINI
    mock_prompt.call_params = Mock()
    mock_prompt.call_params.model_dump.return_value = {"test": "config"}
    return mock_prompt


def test_get_type_str():
    """Test _get_type_str function."""
    from lilypad._utils.functions import _get_type_str

    assert _get_type_str(int) == "int"
    assert _get_type_str(list[int]) == "list[int]"
    assert _get_type_str(dict[str, int]) == "dict[str, int]"


@pytest.mark.asyncio
async def test_create_mirascope_call_async_str(mock_prompt):
    """Test async function returning str."""

    async def fn(text: str) -> str: ...

    mock_provider_call = AsyncMock()
    mock_provider_call.return_value = Mock(content="test")
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(fn, mock_prompt, None)
        assert await result("test") == "test"


@pytest.mark.asyncio
async def test_create_mirascope_call_async_stream(mock_prompt):
    """Test async function with streaming."""
    mock_chunk = Mock(content="chunk")

    async def mock_provider_call(*args, **kwargs):
        async def inner_mock_chunk():
            for chunk in [(mock_chunk, None)]:
                yield chunk

        return inner_mock_chunk()

    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(async_stream_test_fn, mock_prompt, lambda x: x)
        async for content in await result("test"):
            assert content == "chunk"


@pytest.mark.asyncio
async def test_create_mirascope_call_async_message(mock_prompt):
    """Test async function returning Message."""
    mock_response = MockResponse(
        metadata={},
        response=TestResponseModel(message="test"),
        tool_types=None,
        prompt_template=None,
        fn_args={},
        dynamic_config=None,
        messages=[],
        call_params={},
        call_kwargs={},
        start_time=0,
        end_time=0,
    )
    mock_provider_call = AsyncMock(return_value=mock_response)
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(async_message_test_fn, mock_prompt, lambda x: x)
        assert await result("test")


@pytest.mark.asyncio
async def test_create_mirascope_call_async_iterable_model(mock_prompt):
    """Test async function returning Iterable[Model]."""
    mock_provider_call = AsyncMock()
    mock_provider_call.return_value = [TestResponseModel(message="test")]
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(async_iterable_model_test_fn, mock_prompt, None)
        assert await result("test")


def test_create_mirascope_call_sync_str(mock_prompt):
    """Test sync function returning str."""

    def fn(text: str) -> str: ...

    mock_response = Mock(content="test")
    mock_provider_call = Mock(return_value=mock_response)
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(fn, mock_prompt, None)
        assert result("test") == "test"


def test_create_mirascope_call_sync_stream(mock_prompt):
    """Test sync function with streaming."""
    mock_chunk = Mock(content="chunk")

    def mock_provider_call(*args, **kwargs):
        def inner_mock_chunk():
            yield from [(mock_chunk, None)]

        return inner_mock_chunk()

    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(sync_stream_test_fn, mock_prompt, None)
        for content in result("test"):
            assert content == "chunk"


def test_create_mirascope_call_sync_message(mock_prompt):
    """Test sync function returning Message."""
    mock_response = MockResponse(
        metadata={},
        response=Mock(),
        tool_types=None,
        prompt_template=None,
        fn_args={},
        dynamic_config=None,
        messages=[],
        call_params={},
        call_kwargs={},
        start_time=0,
        end_time=0,
    )
    mock_provider_call = Mock(return_value=mock_response)
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(sync_message_test_fn, mock_prompt, None)
        assert result("test")


def test_create_mirascope_call_sync_iterable_model(mock_prompt):
    """Test sync function returning Iterable[Model]."""
    mock_provider_call = Mock(return_value=[TestResponseModel(message="test")])
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(sync_iterable_model_test_fn, mock_prompt, None)
        assert result("test")


def test_create_mirascope_call_invalid_return_type(mock_prompt):
    """Test function with invalid return type."""

    def fn(text: str) -> None: ...  # objectからNoneに変更

    with pytest.raises(ValueError, match="Unsupported return type"):
        mock_provider_call = Mock()
        mock_module = Mock()
        mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

        with patch("lilypad._utils.functions.import_module", return_value=mock_module):
            result = create_mirascope_call(fn, mock_prompt, None)
            result("test")


def test_create_mirascope_call_gemini(mock_gemini_prompt):
    """Test Gemini provider specific functionality."""
    mock_provider_call = Mock(return_value=lambda x: x)
    mock_module = Mock()
    mock_module.call = mock_provider_call

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(sync_test_fn, mock_gemini_prompt, None)
        result("test")
        mock_gemini_prompt.call_params.model_dump.assert_called_with(
            exclude_defaults=True
        )


def test_inspect_arguments_with_args():
    """Test inspecting function with *args."""

    def test_func(*args: int): ...

    arg_types, arg_values = inspect_arguments(test_func, 1, 2, 3)
    assert arg_types == {"args": "int"}
    assert arg_values == {"args": (1, 2, 3)}


def test_inspect_arguments_mixed():
    """Test inspecting function with mixed parameters."""

    def test_func(x: int, *args: str, **kwargs: float): ...

    arg_types, arg_values = inspect_arguments(
        test_func, 1, "a", "b", test1=1.0, test2=2.0
    )
    assert arg_types == {"x": "int", "args": "str", "kwargs": "float"}
    assert arg_values == {
        "x": 1,
        "args": ("a", "b"),
        "kwargs": {"test1": 1.0, "test2": 2.0},
    }


def create_mock_prompt():
    """Helper function to create a consistent mock prompt."""
    mock_prompt = Mock()
    mock_prompt.provider = Mock()
    mock_prompt.provider.value = "openai"
    mock_prompt.template = "test template"
    mock_prompt.model = "test_model"
    mock_prompt.call_params = None
    return mock_prompt


@pytest.mark.asyncio
async def test_create_mirascope_call_async_base_type():
    """Test async function returning base type (str, int, etc)."""

    async def fn(text: str) -> int: ...

    mock_provider_call = AsyncMock(return_value="42")
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    mock_prompt = create_mock_prompt()

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(fn, mock_prompt, None)
        output = await result("test")
        assert output == "42"


def test_create_mirascope_call_sync_base_type():
    """Test sync function returning base type (str, int, etc)."""

    def fn(text: str) -> int: ...

    mock_provider_call = Mock(return_value="42")
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    mock_prompt = create_mock_prompt()

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(fn, mock_prompt, None)
        output = result("test")
        assert output == "42"


def test_create_mirascope_call_with_trace_decorator():
    """Test function with trace decorator."""

    def fn(text: str) -> str: ...

    mock_response = Mock(content="42")
    mock_provider_call = Mock(return_value=mock_response)
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    mock_prompt = create_mock_prompt()
    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(fn, mock_prompt, lambda x: x)
        output = result("test")
        assert output == "42"


@pytest.mark.asyncio
async def test_create_mirascope_call_async_with_trace_decorator():
    """Test async function with trace decorator."""

    async def fn(text: str) -> str: ...

    mock_response = Mock(content="42")
    mock_provider_call = AsyncMock(return_value=mock_response)
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    mock_prompt = create_mock_prompt()

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(fn, mock_prompt, lambda x: x)
        output = await result("test")
        assert output == "42"


def test_create_mirascope_call_model_with_response():
    """Test function returning model with _response attribute."""

    class ResponseModel(TestResponseModel):
        _response: Any = None

    def fn(text: str) -> ResponseModel: ...

    mock_response = ResponseModel(message="test")
    mock_provider_call = Mock(return_value=mock_response)
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    mock_prompt = create_mock_prompt()

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(fn, mock_prompt, None)
        output = result("test")
        assert isinstance(output, ResponseModel)


def test_create_mirascope_call_with_openrouter():
    """Test function with openrouter."""
    mock_prompt = Mock()
    mock_prompt.provider = Mock()
    mock_prompt.provider.value = "openrouter"
    mock_prompt.template = "test template"
    mock_prompt.model = "test_model"
    mock_prompt.call_params = None

    def fn(text: str) -> str: ...

    mock_response = Mock(content="test")
    mock_provider_call = Mock(return_value=mock_response)
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    mock_prompt = create_mock_prompt()

    with patch(
        "lilypad._utils.functions.import_module", return_value=mock_module
    ) as mock_import:
        result = create_mirascope_call(fn, mock_prompt, lambda x: x)
        output = result("test")
        assert output == "test"
        mock_import.assert_called_with("mirascope.core.openai")


@pytest.mark.asyncio
async def test_create_mirascope_call_async_openrouter():
    """Test async function with OpenRouter provider."""

    async def fn(text: str) -> str: ...

    mock_prompt = Mock()
    mock_prompt.provider = Mock(value="openrouter")
    mock_prompt.template = "test template"
    mock_prompt.model = "test_model"
    mock_prompt.call_params = None

    mock_response = Mock(content="test")
    mock_provider_call = AsyncMock(return_value=mock_response)
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with (
        patch("openai.AsyncOpenAI") as mock_async_openai,
        patch("lilypad._utils.functions.import_module", return_value=mock_module),
        patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"}),
    ):
        result = create_mirascope_call(fn, mock_prompt, None)
        output = await result("test")
        assert output == "test"
        mock_async_openai.assert_called_once_with(
            base_url="https://openrouter.ai/api/v1", api_key="test_key"
        )


def test_create_mirascope_call_sync_openrouter():
    """Test sync function with OpenRouter provider."""

    def fn(text: str) -> str: ...

    mock_prompt = Mock()
    mock_prompt.provider = Mock(value="openrouter")
    mock_prompt.template = "test template"
    mock_prompt.model = "test_model"
    mock_prompt.call_params = None

    mock_response = Mock(content="test")
    mock_provider_call = Mock(return_value=mock_response)
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with (
        patch("openai.OpenAI") as mock_openai,
        patch("lilypad._utils.functions.import_module", return_value=mock_module),
        patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"}),
    ):
        result = create_mirascope_call(fn, mock_prompt, None)
        output = result("test")
        assert output == "test"
        mock_openai.assert_called_once_with(
            base_url="https://openrouter.ai/api/v1", api_key="test_key"
        )


@pytest.mark.asyncio
async def test_create_mirascope_call_async_iterable_str():
    """Test async function returning AsyncIterable[str]."""

    async def fn(text: str) -> AsyncIterable[str]: ...

    mock_chunk = Mock(content="chunk")

    async def mock_provider_call(*args, **kwargs):
        async def inner_mock_chunk():
            for chunk in [(mock_chunk, None)]:
                yield chunk

        return inner_mock_chunk()

    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    mock_prompt = create_mock_prompt()

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(fn, mock_prompt, None)
        async for content in await result("test"):
            assert content == "chunk"


def test_create_mirascope_call_sync_iterable_str():
    """Test sync function returning Iterable[str]."""

    def fn(text: str) -> Iterable[str]: ...

    mock_chunk = Mock(content="chunk")

    def mock_provider_call(*args, **kwargs):
        def inner_mock_chunk():
            yield from [(mock_chunk, None)]

        return inner_mock_chunk()

    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    mock_prompt = create_mock_prompt()

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(fn, mock_prompt, lambda x: x)
        for content in result("test"):
            assert content == "chunk"


@pytest.mark.asyncio
async def test_create_mirascope_call_message_with_tool_args(mock_chat_completion):
    """Test function returning Message with tool arguments."""

    async def fn(text: str) -> Message[FormatBook, FormatAuthor]: ...

    mock_response = MockResponse(
        metadata={},
        response=mock_chat_completion,
        tool_types=[FormatBook, FormatAuthor],
        prompt_template=None,
        fn_args={},
        dynamic_config=None,
        messages=[],
        call_params={},
        call_kwargs={},
        start_time=0,
        end_time=0,
    )
    mock_provider_call = AsyncMock(return_value=mock_response)
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    mock_prompt = create_mock_prompt()

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(fn, mock_prompt, lambda x: x)
        response = await result("test")
        assert isinstance(response, Message)


@pytest.mark.asyncio
async def test_create_mirascope_call_custom_message_with_tool_args(
    mock_chat_completion,
):
    """Test function returning Message with tool arguments."""

    async def fn(text: str) -> CustomMessage[FormatBook, FormatAuthor]: ...  # pyright: ignore [reportInvalidTypeArguments]

    mock_response = MockResponse(
        metadata={},
        response=mock_chat_completion,
        tool_types=[FormatBook, FormatAuthor],
        prompt_template=None,
        fn_args={},
        dynamic_config=None,
        messages=[],
        call_params={},
        call_kwargs={},
        start_time=0,
        end_time=0,
    )
    mock_provider_call = AsyncMock(return_value=mock_response)
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    mock_prompt = create_mock_prompt()

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(fn, mock_prompt, lambda x: x)
        response = await result("test")
        assert isinstance(response, Message)


def test_create_mirascope_sync_call_custom_message_with_tool_args(mock_chat_completion):
    """Test function returning Message with tool arguments."""

    def fn(text: str) -> CustomMessage[FormatBook, FormatAuthor]: ...  # pyright: ignore [reportInvalidTypeArguments]

    mock_response = MockResponse(
        metadata={},
        response=mock_chat_completion,
        tool_types=[FormatBook, FormatAuthor],
        prompt_template=None,
        fn_args={},
        dynamic_config=None,
        messages=[],
        call_params={},
        call_kwargs={},
        start_time=0,
        end_time=0,
    )
    mock_provider_call = Mock(return_value=mock_response)
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    mock_prompt = create_mock_prompt()

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(fn, mock_prompt, lambda x: x)
        response = result("test")
        assert isinstance(response, Message)


# Test for async invalid return type
@pytest.mark.asyncio
async def test_create_mirascope_call_async_invalid_return_type():
    """Test async function with invalid return type."""

    async def fn(text: str) -> None: ...

    mock_prompt = Mock()
    mock_prompt.provider = Mock()
    mock_prompt.provider.value = "openai"
    mock_prompt.template = "test template"
    mock_prompt.model = "test_model"
    mock_prompt.call_params = None

    mock_provider_call = AsyncMock()
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with (
        pytest.raises(ValueError, match="Unsupported return type"),
        patch("lilypad._utils.functions.import_module", return_value=mock_module),
    ):
        result = create_mirascope_call(fn, mock_prompt, None)
        await result("test")


# Test for async call with Gemini provider and no call params
@pytest.mark.asyncio
async def test_create_mirascope_call_async_gemini_no_call_params():
    """Test async function with Gemini provider and no call params."""

    async def fn(text: str) -> str: ...

    mock_prompt = Mock()
    mock_prompt.provider = Provider.OPENAI
    mock_prompt.template = "test template"
    mock_prompt.model = "test_model"
    mock_prompt.call_params = None

    mock_provider_call = AsyncMock()
    mock_provider_call.return_value.content = "test"
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(fn, mock_prompt, None)
        response = await result("test")
        assert response == "test"


# Test for sync call with Gemini provider and no call params
def test_create_mirascope_call_sync_gemini_no_call_params():
    """Test sync function with Gemini provider and no call params."""

    def fn(text: str) -> str: ...

    mock_prompt = Mock()
    mock_prompt.provider = Provider.GEMINI
    mock_prompt.template = "test template"
    mock_prompt.model = "test_model"
    mock_prompt.call_params = None

    mock_provider_call = Mock()
    mock_provider_call.return_value.content = "test"
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(fn, mock_prompt, None)
        response = result("test")
        assert response == "test"


# Test for sync Message with tools but no response model
def test_create_mirascope_call_sync_message_with_tools_no_response_model():
    """Test sync function returning Message with tools but no response model."""

    def fn(text: str) -> Message: ...

    # Setup base mocks
    mock_prompt = Mock()
    mock_prompt.provider = Mock()
    mock_prompt.provider.value = "openai"
    mock_prompt.template = "test template"
    mock_prompt.model = "test_model"
    mock_prompt.call_params = None

    # Create a mock response with necessary model fields
    mock_response = MockResponse(
        metadata={},
        response=Mock(),
        tool_types=None,
        prompt_template=None,
        fn_args={},
        dynamic_config=None,
        messages=[],
        call_params={},
        call_kwargs={},
        start_time=0,
        end_time=0,
    )

    mock_provider_call = Mock(return_value=mock_response)
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(fn, mock_prompt, None)
        response = result("test")
        assert isinstance(response, Message)


@pytest.mark.parametrize(
    "is_async,provider",
    [
        (False, Provider.GEMINI),
        (True, Provider.GEMINI),
        (False, Provider.OPENAI),
        (True, Provider.OPENAI),
    ],
)
@pytest.mark.asyncio
async def test_create_mirascope_call_with_call_params(is_async, provider):
    """Test sync/async function with provider and call params."""
    if is_async:

        async def fn(text: str) -> str:  # pyright: ignore [reportRedeclaration]
            ...

        # Setup mock response
        mock_response = Mock()
        mock_response.content = "test"

        # Setup async mock call chain
        def mock_decorator(func: Callable) -> Callable:
            async def wrapper(*args, **kwargs):
                await func(*args, **kwargs)
                return mock_response

            return wrapper

        mock_call = Mock()
        mock_call.return_value = mock_decorator
    else:

        def fn(text: str) -> str: ...

        # Setup mock response
        mock_response = Mock()
        mock_response.content = "test"

        # Setup sync mock call chain

        def mock_decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                func(*args, **kwargs)
                return mock_response

            return wrapper

        mock_call = Mock(return_value=mock_decorator)

    # Setup mock module
    mock_module = Mock()
    mock_module.call = mock_call

    # Set up prompt mock
    mock_prompt = Mock()
    mock_prompt.provider = provider
    mock_prompt.template = "test template"
    mock_prompt.model = "test_model"
    mock_prompt.call_params = Mock()
    mock_prompt.call_params.model_dump = Mock(return_value={"test": "config"})

    fn._prompt_template = "test template"  # pyright: ignore [reportFunctionMemberAccess]
    fn.__mirascope_prompt_template__ = True  # pyright: ignore [reportFunctionMemberAccess]

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(fn, mock_prompt, None)
        if is_async:
            response = await result("test")  # pyright: ignore [reportGeneralTypeIssues]
        else:
            response = result("test")

        assert response == "test"
        # Verify call chain setup
        mock_call.assert_called_once_with(
            model="test_model", json_mode=False, client=None
        )
        # Verify that model_dump was called
        mock_prompt.call_params.model_dump.assert_called_once_with(
            exclude_defaults=True
        )


# Test inspect_arguments with complex type annotations
def test_inspect_arguments_with_complex_types():
    """Test inspecting function with complex type annotations."""
    from typing import Optional, Union

    def fn(
        x: list[dict[str, Any]],  # noqa: UP007
        y: Optional[int],  # noqa: UP007
        z: Union[str, int, None],  # noqa: UP007
        *args: list[str],  # noqa: UP007
        **kwargs: dict[str, float],  # noqa: UP007
    ): ...

    x_val = [{"a": 1}]
    y_val = None
    z_val = "test"
    args_val = (["test"],)
    kwargs_val = {"test": 1.0}

    arg_types, arg_values = inspect_arguments(
        fn, x_val, y_val, z_val, *args_val, **kwargs_val  # pyright: ignore [reportArgumentType]
    )

    assert arg_types == {
        "x": "list[dict[str, Any]]",
        "y": "Optional[int]",
        "z": "Union[str, int, None]",
        "args": "list[str]",
        "kwargs": "dict[str, float]",
    }
    assert arg_values == {
        "x": x_val,
        "y": y_val,
        "z": z_val,
        "args": args_val,
        "kwargs": kwargs_val,
    }


def test_inspect_arguments_with_new_union_syntax():
    """Test inspecting function with complex type annotations."""

    def fn(
        y: int | None,
        z: str | int | None,
    ): ...

    y_val = None
    z_val = "test"

    arg_types, arg_values = inspect_arguments(fn, y_val, z_val)

    assert arg_types == {"y": "int | None", "z": "str | int | None"}

    assert arg_values == {
        "y": y_val,
        "z": z_val,
    }
