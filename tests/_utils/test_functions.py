"""Tests for lilypad._utils.functions module."""

from typing import Any, Iterable, AsyncIterable
from unittest.mock import Mock, patch, AsyncMock

import pytest
from pydantic import BaseModel

from mirascope.core.base import BaseCallResponse
from lilypad import Message
from lilypad._utils.functions import create_mirascope_call, inspect_arguments
from lilypad.server.models import Provider


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

    arg_types, arg_values = inspect_arguments(test_func, test=123)
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
    message: str


class CustomMessage(Message):
    pass


async def async_test_fn(text: str) -> TestResponseModel: ...


def sync_test_fn(text: str) -> TestResponseModel: ...


async def async_stream_test_fn(text: str) -> AsyncIterable[str]: ...


def sync_stream_test_fn(text: str) -> Iterable[str]: ...


async def async_message_test_fn(text: str) -> Message[CustomMessage]: ...


def sync_message_test_fn(text: str) -> Message[CustomMessage]: ...


async def async_iterable_model_test_fn(text: str) -> Iterable[TestResponseModel]: ...


def sync_iterable_model_test_fn(text: str) -> Iterable[TestResponseModel]: ...


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


class MockBaseCallResponse(BaseCallResponse):
    """Mock for BaseCallResponse."""

    @property
    def content(self) -> str:
        return "test content"

    @property
    def finish_reasons(self) -> list[str] | None:
        return None

    @property
    def model(self) -> str | None:
        return None

    @property
    def id(self) -> str | None:
        return None

    @property
    def usage(self) -> Any:
        return None

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

    @property
    def tools(self) -> list[Any] | None:
        return None

    @property
    def tool(self) -> Any | None:
        return None

    @classmethod
    def tool_message_params(cls, tools_and_outputs: list[tuple[Any, Any]]) -> list[Any]:
        return []


@pytest.mark.asyncio
async def test_create_mirascope_call_async_stream(mock_prompt):
    """Test async function with streaming."""
    mock_provider_call = AsyncMock()
    mock_chunk = Mock(content="chunk")
    mock_provider_call.__aiter__ = [(mock_chunk, None)]
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(async_stream_test_fn, mock_prompt, lambda x: x)
        async for content in await result("test"):
            assert content == "chunk"


@pytest.mark.asyncio
async def test_create_mirascope_call_async_message(mock_prompt):
    """Test async function returning Message."""
    mock_response = MockBaseCallResponse(
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
    mock_provider_call = Mock(return_value=[(mock_chunk, None)])
    mock_module = Mock()
    mock_module.call = Mock(return_value=lambda *args, **kwargs: mock_provider_call)

    with patch("lilypad._utils.functions.import_module", return_value=mock_module):
        result = create_mirascope_call(sync_stream_test_fn, mock_prompt, None)
        for content in result("test"):
            assert content == "chunk"


def test_create_mirascope_call_sync_message(mock_prompt):
    """Test sync function returning Message."""
    mock_response = MockBaseCallResponse(
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
