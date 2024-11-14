"""Tests traces decorators."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from lilypad import trace
from lilypad.server.models import (
    FunctionPublic,
    VersionPublic,
)


# Test models
class TestResponse(BaseModel):
    """Test model for custom return type"""

    message: str


class TestModel:
    """Test model for custom return type"""

    def __init__(self, value: str):
        self.value = value

    def model_dump(self):
        """Dump the model to a dictionary"""
        return {"value": self.value}

    def __str__(self):
        return str(self.model_dump())


# Mock fixtures
@pytest.fixture
def mock_lilypad_client():
    """Fixture that mocks the LilypadClient"""
    with patch("lilypad.traces.lilypad_client") as mock:
        # Create function model
        function = FunctionPublic(
            id=1,
            name="test_function",
            hash="test_hash",
            code="test code",
            arg_types={"param": "str"},
            project_id=1,
        )

        # Create version with required fields
        version = VersionPublic(
            id=1,
            version_num=1,
            project_id=1,
            function_id=1,
            function_name="test_function",
            function_hash="test_hash",
            function=function,
            is_active=True,
            prompt=None,
            spans=[],
        )

        mock.get_or_create_function_version.return_value = version
        mock.project_id = 1
        yield mock


@pytest.fixture
def mock_get_tracer():
    """Fixture that mocks the get_tracer function"""
    with patch("lilypad.traces.get_tracer") as mock_tracer:
        # Configure the mock span
        mock_span = MagicMock()
        mock_span.set_attributes.return_value = None
        mock_span.__enter__.return_value = mock_span
        mock_span.__exit__.return_value = None

        # Configure the mock tracer
        mock_tracer_instance = MagicMock()
        mock_tracer_instance.start_as_current_span.return_value = mock_span
        mock_tracer.return_value = mock_tracer_instance

        yield mock_tracer


def test_trace_sync_with_model_return(mock_lilypad_client, mock_get_tracer):
    """Test tracing of a synchronous function with custom model return"""

    @trace()
    def test_function() -> TestModel:
        return TestModel("test value")

    result = test_function()

    assert isinstance(result, TestModel)
    assert result.value == "test value"
    mock_get_tracer.return_value.start_as_current_span.assert_called_once()
    mock_span = mock_get_tracer.return_value.start_as_current_span.return_value.__enter__.return_value
    mock_span.set_attributes.assert_called_once()
    attrs = mock_span.set_attributes.call_args[0][0]
    assert attrs["lilypad.output"] == "{'value': 'test value'}"


def test_trace_sync_with_pydantic_return(mock_lilypad_client, mock_get_tracer):
    """Test tracing of a synchronous function with Pydantic model return"""

    @trace()
    def test_function() -> TestResponse:
        return TestResponse(message="hello")

    result = test_function()

    assert isinstance(result, TestResponse)
    assert result.message == "hello"
    mock_get_tracer.return_value.start_as_current_span.assert_called_once()
    mock_span = mock_get_tracer.return_value.start_as_current_span.return_value.__enter__.return_value
    mock_span.set_attributes.assert_called_once()
    attrs = mock_span.set_attributes.call_args[0][0]
    assert attrs["lilypad.output"] == str({"message": "hello"})


@pytest.mark.asyncio
async def test_trace_async_function(mock_lilypad_client, mock_get_tracer):
    """Test tracing of an asynchronous function with string return"""

    @trace()
    async def test_function(param: str) -> str:
        return f"Hello {param}"

    result = await test_function("World")

    assert result == "Hello World"
    mock_get_tracer.return_value.start_as_current_span.assert_called_once()
    mock_span = mock_get_tracer.return_value.start_as_current_span.return_value.__enter__.return_value
    mock_span.set_attributes.assert_called_once()
    attrs = mock_span.set_attributes.call_args[0][0]
    assert attrs["lilypad.function_name"] == "test_function"
    assert attrs["lilypad.version_id"] == 1
    assert attrs["lilypad.output"] == "Hello World"
    assert attrs["lilypad.is_async"]


@pytest.mark.asyncio
async def test_trace_async_with_model_return(mock_lilypad_client, mock_get_tracer):
    """Test tracing of an asynchronous function with custom model return"""

    @trace()
    async def test_function() -> TestModel:
        return TestModel("test value")

    result = await test_function()

    assert isinstance(result, TestModel)
    assert result.value == "test value"
    mock_get_tracer.return_value.start_as_current_span.assert_called_once()
    mock_span = mock_get_tracer.return_value.start_as_current_span.return_value.__enter__.return_value
    mock_span.set_attributes.assert_called_once()
    attrs = mock_span.set_attributes.call_args[0][0]
    assert attrs["lilypad.output"] == "{'value': 'test value'}"


@pytest.mark.asyncio
async def test_trace_async_with_pydantic_return(mock_lilypad_client, mock_get_tracer):
    """Test tracing of an asynchronous function with Pydantic model return"""

    @trace()
    async def test_function() -> TestResponse:
        return TestResponse(message="hello")

    result = await test_function()

    assert isinstance(result, TestResponse)
    assert result.message == "hello"
    mock_get_tracer.return_value.start_as_current_span.assert_called_once()
    mock_span = mock_get_tracer.return_value.start_as_current_span.return_value.__enter__.return_value
    mock_span.set_attributes.assert_called_once()
    attrs = mock_span.set_attributes.call_args[0][0]
    assert attrs["lilypad.output"] == str({"message": "hello"})


def test_trace_handles_errors(mock_lilypad_client, mock_get_tracer):
    """Test proper error handling in traced functions"""

    @trace()
    def test_function():
        raise ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        test_function()


@pytest.mark.asyncio
async def test_trace_handles_async_errors(mock_lilypad_client, mock_get_tracer):
    """Test proper error handling in async traced functions"""

    @trace()
    async def test_function():
        raise ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        await test_function()


def test_version_tracking(mock_lilypad_client):
    """Test that function versioning works correctly"""

    @trace()
    def test_function(param: str) -> str:
        return f"Hello {param}"

    test_function("World")

    mock_lilypad_client.get_or_create_function_version.assert_called_once()
    call_args = mock_lilypad_client.get_or_create_function_version.call_args
    assert call_args[0][0].__name__ == "test_function"
    assert isinstance(call_args[0][1], dict)
    assert "param" in call_args[0][1]
