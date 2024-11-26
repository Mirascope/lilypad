"""Tests for lilypad._utils.functions module."""

import os
from collections.abc import AsyncIterable, Callable, Iterable
from typing import Any, TypeVar
from unittest.mock import AsyncMock, Mock, patch

import pytest
from mirascope.core.base.tool import BaseTool
from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion import ChatCompletion, Choice
from pydantic import BaseModel

from lilypad import Message
from lilypad._utils.functions import create_mirascope_call, inspect_arguments
from lilypad.server.models import Provider

# Type variable for response models
ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


class TestResponseModel(BaseModel):
    """Mock response model for testing"""

    message: str


class FormatBook(BaseTool):
    """Mock tool that formats the book"""

    title: str
    author: str


# Mock test functions
async def async_test_fn(text: str) -> TestResponseModel:  # pyright: ignore [reportReturnType]
    """Mock async test function."""
    pass


def sync_test_fn(text: str) -> TestResponseModel:  # pyright: ignore [reportReturnType]
    """Mock sync test function."""
    pass


async def async_stream_test_fn(text: str) -> AsyncIterable[TestResponseModel]:  # pyright: ignore [reportReturnType]
    """Mock async stream test function."""
    pass


async def async_stream_str_test_fn(text: str) -> AsyncIterable[str]:  # pyright: ignore [reportReturnType]
    """Mock async stream test function."""
    pass


def sync_stream_test_fn(text: str) -> Iterable[TestResponseModel]:  # pyright: ignore [reportReturnType]
    """Mock sync stream test function."""
    pass


def sync_stream_test_str_fn(text: str) -> Iterable[str]:  # pyright: ignore [reportReturnType]
    """Mock sync stream test function."""
    pass


async def async_message_test_fn(text: str) -> Message[Any]:  # pyright: ignore [reportReturnType]
    """Mock async message test function."""
    pass


def sync_message_test_fn(text: str) -> Message[Any]:  # pyright: ignore [reportReturnType]
    """Mock sync message test function."""
    pass


async def async_iterable_model_test_fn(text: str) -> Iterable[TestResponseModel]:  # pyright: ignore [reportReturnType]
    """Mock async iterable model test function."""
    pass


def sync_iterable_model_test_fn(text: str) -> Iterable[TestResponseModel]:  # pyright: ignore [reportReturnType]
    """Mock sync iterable model test function."""
    pass


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


def test_get_type_str_non_generic():
    """Test handling of non-generic types without __name__ attribute."""

    class CustomType:
        def __str__(self):
            return "CustomType"

    # Test case for custom type without __name__ attribute
    custom_type = CustomType()
    arg_types, arg_values = inspect_arguments(lambda x: None, custom_type)
    assert arg_types == {"x": "CustomType"}


def test_get_type_str_generic_types():
    """Test handling of various generic types."""

    def test_func(x: list[int], y: dict[str, int], z: set): ...

    # Test various generic types including List, Dict, and Set
    arg_types, _ = inspect_arguments(test_func, [1, 2, 3], {"a": 1}, {1, 2, 3})
    assert arg_types == {
        "x": "list[int]",  # Changed from 'List[int]'
        "y": "dict[str, int]",  # Changed from 'Dict[str, int]'
        "z": "set",  # Changed from 'Set'
    }


def test_get_type_str_custom_generic():
    """Test handling of custom generic types."""
    from typing import Generic, TypeVar

    T = TypeVar("T")

    class GenericContainer(Generic[T]):
        def __init__(self, value: T):
            self.value = value

    def test_func(x: GenericContainer[int]): ...

    container = GenericContainer(42)
    arg_types, _ = inspect_arguments(test_func, container)
    assert arg_types == {"x": "GenericContainer[int]"}


def test_get_type_str_nested_generics():
    """Test handling of nested generic types."""

    def test_func(x: list[dict[str, int]]): ...

    # Test nested generic types (List containing Dict)
    arg_types, _ = inspect_arguments(test_func, [{"a": 1}, {"b": 2}])
    assert arg_types == {
        "x": "list[dict[str, int]]"
    }  # Changed from 'List[Dict[str, int]]'


def test_get_type_str_empty_generic():
    """Test handling of generic types without type parameters."""

    def test_func(x: list, y: dict, z: set): ...

    # Test generic types without specified type parameters
    arg_types, _ = inspect_arguments(test_func, [], {}, set())
    assert arg_types == {
        "x": "list",  # Changed from 'List'
        "y": "dict",  # Changed from 'Dict'
        "z": "set",  # Changed from 'Set'
    }


@pytest.mark.asyncio
async def test_create_mirascope_call_async_str(create_mock_prompt):
    """Test async function returning str."""

    async def fn(text: str) -> str: ...

    mock_provider_call = AsyncMock()
    mock_provider_call.return_value = Mock(content="test")
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    mock_prompt = create_mock_prompt()

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(fn, mock_prompt, None)
        assert await result("test") == "test"


@pytest.mark.asyncio
async def test_create_mirascope_call_async_stream_with_model(create_mock_prompt):
    """Test async function with streaming."""

    async def mock_provider_call(*args, **kwargs):
        async def inner_mock_chunk():
            for chunk in [("chunk", None)]:
                yield chunk

        return inner_mock_chunk()

    mock_prompt = create_mock_prompt()

    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(async_stream_test_fn, mock_prompt, lambda x: x)
        async for content, _ in await result("test"):
            assert content == "chunk"


@pytest.mark.asyncio
async def test_create_mirascope_call_async_stream_with_str(create_mock_prompt):
    """Test async function with streaming."""
    mock_chunk = Mock(content="chunk")

    async def mock_provider_call(*args, **kwargs):
        async def inner_mock_chunk():
            for chunk in [(mock_chunk, None)]:
                yield chunk

        return inner_mock_chunk()

    mock_prompt = create_mock_prompt()

    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(
            async_stream_str_test_fn, mock_prompt, lambda x: x
        )
        async for content in await result("test"):
            assert content == "chunk"


@pytest.mark.asyncio
async def test_create_mirascope_call_async_message(create_mock_prompt, mock_response):
    """Test async function returning Message."""
    mock_prompt = create_mock_prompt()
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
    create_mock_prompt, mock_response, format_book, format_author
):
    """Test function returning Message with tool arguments."""
    mock_prompt = create_mock_prompt()

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


def test_create_mirascope_call_sync_str(create_mock_prompt):
    """Test sync function returning str."""

    def fn(text: str) -> str: ...

    mock_prompt = create_mock_prompt()
    mock_response = Mock(content="test")
    mock_provider_call = Mock(return_value=mock_response)
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(fn, mock_prompt, None)
        assert result("test") == "test"


def test_create_mirascope_call_sync_stream_with_str(create_mock_prompt):
    """Test sync function with streaming."""
    mock_chunk = Mock(content="chunk")

    mock_prompt = create_mock_prompt()

    def mock_provider_call(*args, **kwargs):
        def inner_mock_chunk():
            yield from [(mock_chunk, None)]

        return inner_mock_chunk()

    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(
            sync_stream_test_str_fn, mock_prompt, lambda x: x
        )
        for content in result("test"):
            assert content == "chunk"


def test_create_mirascope_call_sync_stream(create_mock_prompt):
    """Test sync function with streaming."""
    mock_prompt = create_mock_prompt()

    def mock_provider_call(*args, **kwargs):
        def inner_mock_chunk():
            yield from [("chunk", None)]

        return inner_mock_chunk()

    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(sync_stream_test_fn, mock_prompt, lambda x: x)
        for content, _ in result("test"):
            assert content == "chunk"


def test_create_mirascope_call_sync_message(create_mock_prompt, mock_response):
    """Test sync function returning Message."""
    mock_prompt = create_mock_prompt()
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
    create_mock_prompt, mock_response, test_response_model
):
    """Test sync function returning Iterable[Model]."""
    mock_prompt = create_mock_prompt()
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

    with (
        patch("openai.OpenAI") as mock_openai,
        patch("lilypad._utils.functions.import_module", return_value=mock_module),
        patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"}),
    ):
        result = create_mirascope_call(fn, mock_prompt, lambda x: x)
        output = result("test")
        assert output == "test"
        mock_openai.assert_called_once_with(
            base_url="https://openrouter.ai/api/v1", api_key="test_key"
        )


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
        z: str | int | None | list,
        zz,
        *args: list[str],
        **kwargs: dict[str, float],
    ): ...

    x_val = [{"a": 1}]
    y_val = None
    z_val = "test"
    zz = object()
    args_val = (["test"],)
    kwargs_val = {"test": 1.0}

    arg_types, arg_values = inspect_arguments(
        fn,
        x_val,
        y_val,
        z_val,
        zz,
        *args_val,
        **kwargs_val,
    )

    assert arg_types == {
        "x": "list[dict[str, Any]]",
        "y": "Optional[int]",
        "z": "Union[str, int, None, list]",
        "zz": "object",
        "args": "list[str]",
        "kwargs": "dict[str, float]",
    }

    assert arg_values == {
        "x": x_val,
        "y": y_val,
        "z": z_val,
        "zz": zz,
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


@pytest.mark.asyncio
async def test_create_mirascope_call_async_custom_message_class(
    create_mock_prompt, mock_response
):
    """Test async function returning a custom Message class."""

    class CustomMessageType(Message):
        """Custom message type for testing."""

        pass

    async def fn(text: str) -> CustomMessageType:  # pyright: ignore [reportReturnType]
        """Test function returning custom message type."""
        pass

    mock_prompt = create_mock_prompt()

    mock_response_instance = mock_response(
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
        result = create_mirascope_call(fn, mock_prompt, None)
        response = await result("test")
        assert isinstance(response, Message)


def test_create_mirascope_call_sync_custom_message_class(
    create_mock_prompt, mock_response
):
    """Test sync function returning a custom Message class."""

    class CustomMessageType(Message):
        """Custom message type for testing."""

        pass

    def fn(text: str) -> CustomMessageType:  # pyright: ignore [reportReturnType]
        """Test function returning custom message type."""
        pass

    mock_prompt = create_mock_prompt()

    mock_response_instance = mock_response(
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


def test_create_mirascope_call_invalid_return_type(create_mock_prompt):
    """Test function with invalid return type."""

    def fn(text: str) -> None: ...

    mock_prompt = create_mock_prompt()
    with pytest.raises(ValueError, match="Unsupported return type"):
        mock_provider_call = Mock()
        mock_module = Mock()
        mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

        with patch("lilypad._utils.functions.import_module", return_value=mock_module):
            result = create_mirascope_call(fn, mock_prompt, None)
            result("test")


@pytest.mark.asyncio
async def test_create_mirascope_async_call_invalid_return_type(create_mock_prompt):
    """Test function with invalid return type."""

    async def fn(text: str) -> None: ...

    mock_prompt = create_mock_prompt()
    with pytest.raises(ValueError, match="Unsupported return type"):
        mock_provider_call = AsyncMock()
        mock_module = Mock()
        mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

        with patch("lilypad._utils.functions.import_module", return_value=mock_module):
            result = create_mirascope_call(fn, mock_prompt, None)
            await result("test")


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


@pytest.mark.asyncio
async def test_create_mirascope_call_async_base_type(create_mock_prompt):
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


def test_create_mirascope_call_sync_base_type(create_mock_prompt):
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


def test_create_mirascope_call_with_trace_decorator(create_mock_prompt):
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
async def test_create_mirascope_call_async_with_trace_decorator(create_mock_prompt):
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
