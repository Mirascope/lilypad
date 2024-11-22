"""Tests for lilypad._utils.functions module."""

import os
from collections.abc import AsyncIterable, Iterable
from typing import Any, TypeVar
from unittest.mock import AsyncMock, Mock, patch

import pytest
from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion import ChatCompletion, Choice
from pydantic import BaseModel

from lilypad import Message
from lilypad._utils.functions import create_mirascope_call, inspect_arguments
from lilypad.server.models import Provider

# Type variable for response models
ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


# Mock test functions
async def async_test_fn(text: str) -> Any:
    """Mock async test function."""
    pass


def sync_test_fn(text: str) -> Any:
    """Mock sync test function."""
    pass


async def async_stream_test_fn(text: str) -> AsyncIterable[str]:  # pyright: ignore [reportReturnType]
    """Mock async stream test function."""
    pass


def sync_stream_test_fn(text: str) -> Iterable[str]:  # pyright: ignore [reportReturnType]
    """Mock sync stream test function."""
    pass


async def async_message_test_fn(text: str) -> Message[Any]:  # pyright: ignore [reportReturnType]
    """Mock async message test function."""
    pass


def sync_message_test_fn(text: str) -> Message[Any]:  # pyright: ignore [reportReturnType]
    """Mock sync message test function."""
    pass


async def async_iterable_model_test_fn(text: str) -> Iterable[BaseModel]:  # pyright: ignore [reportReturnType]
    """Mock async iterable model test function."""
    pass


def sync_iterable_model_test_fn(text: str) -> Iterable[BaseModel]:  # pyright: ignore [reportReturnType]
    """Mock sync iterable model test function."""
    pass


# Test fixtures
@pytest.fixture
def mock_prompt():
    """Create a mock prompt with default OpenAI provider settings."""
    prompt = Mock()
    prompt.provider = Mock()
    prompt.provider.value = "openai"
    prompt.template = "test template"
    prompt.model = "test_model"
    prompt.call_params = None
    return prompt


@pytest.fixture
def mock_gemini_prompt(mock_prompt):
    """Create a mock prompt with Gemini provider settings."""
    mock_prompt.provider = Provider.GEMINI
    mock_prompt.call_params = Mock()
    mock_prompt.call_params.model_dump.return_value = {"test": "config"}
    return mock_prompt


# Test cases
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
async def test_create_mirascope_call_async_message(mock_prompt, mock_response):
    """Test async function returning Message."""
    MockResponseClass = mock_response
    mock_response_instance = MockResponseClass(
        metadata={},
        response=ChatCompletion(
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
        ),
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

    mock_provider_call = AsyncMock(return_value=mock_response_instance)
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(async_message_test_fn, mock_prompt, lambda x: x)
        assert await result("test")


@pytest.mark.asyncio
async def test_create_mirascope_call_message_with_tool_args(
    mock_prompt, mock_response, format_book, format_author
):
    """Test function returning Message with tool arguments."""

    async def fn(text: str) -> Message[Any]: ...

    MockResponseClass = mock_response
    mock_response_instance = MockResponseClass(
        metadata={},
        response=ChatCompletion(
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
        ),
        tool_types=[format_book, format_author],
        prompt_template=None,
        fn_args={},
        dynamic_config=None,
        messages=[],
        call_params={},
        call_kwargs={},
        start_time=0,
        end_time=0,
    )

    mock_provider_call = AsyncMock(return_value=mock_response_instance)
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(fn, mock_prompt, lambda x: x)
        response = await result("test")
        assert isinstance(response, Message)


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
        result = create_mirascope_call(sync_stream_test_fn, mock_prompt, lambda x: x)
        for content in result("test"):
            assert content == "chunk"


def test_create_mirascope_call_sync_message(mock_prompt, mock_response):
    """Test sync function returning Message."""
    MockResponseClass = mock_response
    mock_response_instance = MockResponseClass(
        metadata={},
        response=ChatCompletion(
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
        ),
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

    mock_provider_call = Mock(return_value=mock_response_instance)
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(sync_message_test_fn, mock_prompt, lambda x: x)
        assert result("test")


def test_create_mirascope_call_sync_iterable_model(
    mock_prompt, mock_response, test_response_model
):
    """Test sync function returning Iterable[Model]."""
    TestResponseModel = test_response_model
    test_instance = TestResponseModel(message="test")

    def test_fn(text: str) -> Iterable[TestResponseModel]:  # pyright: ignore [reportInvalidTypeForm, reportReturnType]
        """Local test function with concrete return type."""
        pass

    # Setup mock to return an iterable containing the instance
    mock_provider_call = Mock(return_value=[test_instance])
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(
            test_fn,  # Use the local function with concrete type
            mock_prompt,
            None,
        )
        response = result("test")
        assert isinstance(response, list)  # Verify we get a list back
        assert len(response) == 1  # Verify we get one item
        assert isinstance(response[0], TestResponseModel)  # Verify the type
        assert response[0].message == "test"  # Verify the content


def test_create_mirascope_call_with_openrouter():
    """Test function with openrouter provider."""
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


def test_inspect_arguments_with_complex_types():
    """Test inspecting function with complex type annotations.
    Tests both traditional syntax (Optional/Union) and new union operator syntax (|).
    """

    # Test with traditional syntax
    def fn(
        x: list[dict[str, Any]],
        y: int | None,
        z: str | int | None,
        *args: list[str],
        **kwargs: dict[str, float],
    ): ...

    x_val = [{"a": 1}]
    y_val = None
    z_val = "test"
    args_val = (["test"],)
    kwargs_val = {"test": 1.0}

    arg_types, arg_values = inspect_arguments(
        fn,
        x_val,
        y_val,
        z_val,
        *args_val,
        **kwargs_val,
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
    """Test inspecting function with new union syntax (Python 3.10+)."""

    def fn(
        y: int | None,
        z: str | int | None,
    ): ...

    y_val = None
    z_val = "test"

    arg_types, arg_values = inspect_arguments(fn, y_val, z_val)

    # Note: We expect the traditional syntax in the output
    assert arg_types == {
        "y": "Optional[int]",
        "z": "Union[str, int, None]",
    }

    assert arg_values == {
        "y": y_val,
        "z": z_val,
    }
