"""Tests to cover missing lines in middleware.py."""

import base64
from io import BytesIO
from uuid import UUID, uuid4
from unittest.mock import MagicMock, patch, Mock, AsyncMock
from typing import Any

import pytest
import orjson
from pydantic import BaseModel
from opentelemetry.trace import Span, Status, StatusCode

from lilypad._utils.middleware import (
    PIL,
    SpanContextHolder,
    _get_custom_context_manager,
    create_mirascope_middleware,
    _handle_error,
    _handle_error_async,
    _set_call_response_attributes,
    _set_response_model_attributes,
    safe_serialize,
    bytes_serializer,
)
from lilypad.generated.types.function_public import FunctionPublic


def test_pil_fallback_implementation():
    """Test the PIL fallback implementation when PIL is not available."""
    # Test the fallback WebPImageFile save method
    webp_file = PIL.WebPImagePlugin.WebPImageFile()
    
    with pytest.raises(NotImplementedError, match="Pillow is not installed"):
        webp_file.save("test.webp")


def test_span_context_holder_set_and_get():
    """Test SpanContextHolder set_span_context and span_context property."""
    holder = SpanContextHolder()
    
    # Initially should be None
    assert holder.span_context is None
    
    # Mock a span and test setting
    mock_span = Mock()
    mock_span_context = Mock()
    mock_span.get_span_context.return_value = mock_span_context
    
    holder.set_span_context(mock_span)
    assert holder.span_context == mock_span_context


def test_span_context_holder_property():
    """Test SpanContextHolder span_context property access."""
    holder = SpanContextHolder()
    
    # Test the property getter when no span context is set
    assert holder.span_context is None


@patch("lilypad._utils.middleware.get_settings")
@patch("lilypad._utils.middleware.get_tracer")
def test_get_custom_context_manager_serialization_error(mock_get_tracer, mock_get_settings):
    """Test _get_custom_context_manager with serialization errors."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_get_settings.return_value = mock_settings
    
    mock_tracer = Mock()
    mock_span = Mock()
    mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
    mock_get_tracer.return_value = mock_tracer
    
    # Create arg_values that will cause serialization errors
    class UnserializableClass:
        def __init__(self):
            self.circular = self
    
    arg_values = {
        "good_arg": "test",
        "bad_arg": UnserializableClass(),
    }
    arg_types = {"good_arg": "str", "bad_arg": "UnserializableClass"}
    
    context_manager_factory = _get_custom_context_manager(
        function=None,
        arg_types=arg_types,
        arg_values=arg_values,
        is_async=False,
    )
    
    # Mock function to pass to context manager
    mock_fn = Mock()
    mock_fn.__name__ = "test_function"
    
    # Test that context manager handles serialization errors gracefully
    context_manager = context_manager_factory(mock_fn)
    
    with context_manager as span:
        assert span == mock_span


@patch("lilypad._utils.middleware.get_settings")
def test_get_custom_context_manager_with_current_span(mock_get_settings):
    """Test _get_custom_context_manager when current_span is provided."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_get_settings.return_value = mock_settings
    
    current_span = Mock()
    
    context_manager_factory = _get_custom_context_manager(
        function=None,
        arg_types={},
        arg_values={},
        is_async=False,
        current_span=current_span,
    )
    
    mock_fn = Mock()
    mock_fn.__name__ = "test_function"
    
    context_manager = context_manager_factory(mock_fn)
    
    # Should use the provided current_span instead of creating new one
    with context_manager as span:
        assert span == current_span


@patch("lilypad._utils.middleware.get_settings")
@patch("lilypad._utils.middleware.get_tracer")
def test_get_custom_context_manager_creates_new_span(mock_get_tracer, mock_get_settings):
    """Test _get_custom_context_manager when no current_span is provided."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_get_settings.return_value = mock_settings
    
    mock_tracer = Mock()
    mock_span = Mock()
    mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
    mock_get_tracer.return_value = mock_tracer
    
    context_manager_factory = _get_custom_context_manager(
        function=None,
        arg_types={},
        arg_values={},
        is_async=False,
        current_span=None,  # No current span provided
    )
    
    mock_fn = Mock()
    mock_fn.__name__ = "test_function"
    
    context_manager = context_manager_factory(mock_fn)
    
    # Should create a new span
    with context_manager as span:
        assert span == mock_span
        mock_get_tracer.assert_called_once_with("lilypad")


def test_handle_error():
    """Test _handle_error function."""
    mock_span = Mock()
    test_error = ValueError("Test error")
    
    _handle_error(mock_span, test_error)
    
    # Should set span status to error
    mock_span.set_status.assert_called_once_with(Status(StatusCode.ERROR, "Test error"))


async def test_handle_error_async():
    """Test _handle_error_async function."""
    mock_span = Mock()
    test_error = ValueError("Test async error")
    
    await _handle_error_async(mock_span, test_error)
    
    # Should set span status to error
    mock_span.set_status.assert_called_once_with(Status(StatusCode.ERROR, "Test async error"))


def test_set_call_response_attributes_with_none_response():
    """Test _set_call_response_attributes when response is None."""
    mock_span = Mock()
    
    _set_call_response_attributes(mock_span, None, "test")
    
    # Should handle None response gracefully
    mock_span.set_attribute.assert_called()


def test_set_call_response_attributes_with_message_param():
    """Test _set_call_response_attributes with message param."""
    mock_span = Mock()
    
    # Mock a response that has message param
    mock_response = Mock()
    mock_response.message_param = {"role": "assistant", "content": "test response"}
    
    _set_call_response_attributes(mock_span, mock_response, "test")
    
    # Should set attributes
    mock_span.set_attribute.assert_called()


def test_set_response_model_attributes_with_none_response():
    """Test _set_response_model_attributes when response is None."""
    mock_span = Mock()
    
    _set_response_model_attributes(mock_span, None, "test")
    
    # Should handle None response gracefully
    mock_span.set_attribute.assert_called()


def test_set_response_model_attributes_with_response_model():
    """Test _set_response_model_attributes with actual response model."""
    mock_span = Mock()
    
    # Mock a response that has response_model
    mock_response = Mock()
    mock_response.response_model = {"key": "value"}
    
    _set_response_model_attributes(mock_span, mock_response, "test")
    
    # Should set attributes
    mock_span.set_attribute.assert_called()


def test_safe_serialize_with_error():
    """Test safe_serialize when serialization raises an error."""
    # Create an object that will cause serialization error
    class UnserializableObject:
        def __init__(self):
            self.circular = self
    
    obj = UnserializableObject()
    result = safe_serialize(obj)
    
    # Should return error message when serialization fails
    assert "could not serialize" in result or result == "could not serialize"


def test_safe_serialize_success():
    """Test safe_serialize with a serializable object."""
    obj = {"key": "value", "number": 42}
    result = safe_serialize(obj)
    
    # Should successfully serialize
    assert isinstance(result, str)
    assert "key" in result
    assert "value" in result


def test_bytes_serializer():
    """Test bytes_serializer function."""
    test_bytes = b"test binary data"
    result = bytes_serializer(test_bytes)
    
    # Should convert bytes to base64 string
    expected = base64.b64encode(test_bytes).decode("utf-8")
    assert result == expected


def test_bytes_serializer_with_non_bytes():
    """Test bytes_serializer with non-bytes input."""
    # Should handle non-bytes input gracefully
    result = bytes_serializer("not bytes")
    assert result == "not bytes"


@patch("lilypad._utils.middleware.get_settings")
def test_get_custom_context_manager_with_decorator_tags(mock_get_settings):
    """Test _get_custom_context_manager with decorator tags."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_get_settings.return_value = mock_settings
    
    current_span = Mock()
    decorator_tags = ["tag1", "tag2"]
    
    context_manager_factory = _get_custom_context_manager(
        function=None,
        arg_types={},
        arg_values={},
        is_async=False,
        current_span=current_span,
        decorator_tags=decorator_tags,
    )
    
    mock_fn = Mock()
    mock_fn.__name__ = "test_function"
    
    context_manager = context_manager_factory(mock_fn)
    
    with context_manager as span:
        # Should set decorator tags as attributes
        current_span.set_attributes.assert_called()


@patch("lilypad._utils.middleware.middleware_factory")
def test_create_mirascope_middleware_basic(mock_middleware_factory):
    """Test create_mirascope_middleware basic functionality."""
    mock_middleware = Mock()
    mock_middleware_factory.return_value = mock_middleware
    
    function = Mock()
    arg_types = {"arg1": "str"}
    arg_values = {"arg1": "value1"}
    
    result = create_mirascope_middleware(
        function=function,
        arg_types=arg_types,
        arg_values=arg_values,
        is_async=False,
        prompt_template="test template",
        project_uuid="test-project-uuid",
    )
    
    # Should call middleware_factory with custom context manager
    mock_middleware_factory.assert_called_once()
    assert result == mock_middleware


@patch("lilypad._utils.middleware.middleware_factory")
def test_create_mirascope_middleware_async(mock_middleware_factory):
    """Test create_mirascope_middleware for async functions."""
    mock_middleware = Mock()
    mock_middleware_factory.return_value = mock_middleware
    
    function = Mock()
    arg_types = {"arg1": "str"}
    arg_values = {"arg1": "value1"}
    
    result = create_mirascope_middleware(
        function=function,
        arg_types=arg_types,
        arg_values=arg_values,
        is_async=True,
        prompt_template="test template",
        project_uuid="test-project-uuid",
    )
    
    # Should call middleware_factory for async
    mock_middleware_factory.assert_called_once()
    assert result == mock_middleware


def test_span_context_holder_initial_state():
    """Test SpanContextHolder initial state."""
    holder = SpanContextHolder()
    
    # Initially _span_context should be None
    assert holder._span_context is None
    assert holder.span_context is None


@patch("lilypad._utils.middleware.fast_jsonable")
def test_get_custom_context_manager_with_orjson_error(mock_fast_jsonable):
    """Test _get_custom_context_manager when orjson.JSONEncodeError is raised."""
    mock_fast_jsonable.side_effect = orjson.JSONEncodeError("JSON encode error")
    
    with patch("lilypad._utils.middleware.get_settings") as mock_get_settings:
        mock_settings = Mock()
        mock_settings.project_id = "test-project"
        mock_get_settings.return_value = mock_settings
        
        current_span = Mock()
        
        context_manager_factory = _get_custom_context_manager(
            function=None,
            arg_types={},
            arg_values={"arg": "value"},
            is_async=False,
            current_span=current_span,
        )
        
        mock_fn = Mock()
        mock_fn.__name__ = "test_function"
        
        context_manager = context_manager_factory(mock_fn)
        
        # Should handle orjson.JSONEncodeError and use "could not serialize"
        with context_manager as span:
            assert span == current_span


def test_set_call_response_attributes_attribute_error():
    """Test _set_call_response_attributes when attribute access fails."""
    mock_span = Mock()
    
    # Create a response object that raises AttributeError for message_param
    class BadResponse:
        @property
        def message_param(self):
            raise AttributeError("No message_param")
    
    response = BadResponse()
    
    # Should handle AttributeError gracefully
    _set_call_response_attributes(mock_span, response, "test")
    
    mock_span.set_attribute.assert_called()


def test_set_response_model_attributes_attribute_error():
    """Test _set_response_model_attributes when attribute access fails."""
    mock_span = Mock()
    
    # Create a response object that raises AttributeError for response_model
    class BadResponse:
        @property
        def response_model(self):
            raise AttributeError("No response_model")
    
    response = BadResponse()
    
    # Should handle AttributeError gracefully
    _set_response_model_attributes(mock_span, response, "test")
    
    mock_span.set_attribute.assert_called()