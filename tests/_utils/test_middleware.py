"""Tests for the middleware module in the _utils package."""

import base64
import json
from io import BytesIO
from unittest.mock import MagicMock, patch
from uuid import UUID

import PIL.Image
import PIL.WebPImagePlugin
import pytest
from pydantic import BaseModel

from lilypad._utils import encode_gemini_part
from lilypad._utils.middleware import (
    _get_custom_context_manager,
    _handle_call_response,
    _handle_call_response_async,
    _handle_response_model,
    _handle_response_model_async,
    _handle_stream,
    _handle_stream_async,
    _handle_structured_stream,
    _handle_structured_stream_async,
    _serialize_proto_data,
    _set_call_response_attributes,
    _set_response_model_attributes,
    create_mirascope_middleware,
)


def test_encode_gemini_part_with_string():
    """Test encode_gemini_part with a string input."""
    input_part = "some string"
    output = encode_gemini_part(input_part)
    assert output == input_part


def test_encode_gemini_part_with_dict_binary_data():
    """Test encode_gemini_part with a dict containing binary data."""
    input_part = {
        "mime_type": "application/octet-stream",
        "data": b"\x00\x01\x02",
    }
    output = encode_gemini_part(input_part)
    assert output["mime_type"] == "application/octet-stream"  # pyright: ignore [reportArgumentType]
    assert output["data"] == base64.b64encode(b"\x00\x01\x02").decode("utf-8")  # pyright: ignore [reportArgumentType]


def test_encode_gemini_part_with_dict_other():
    """Test encode_gemini_part with a generic dict."""
    input_part = {"key": "value"}
    output = encode_gemini_part(input_part)
    assert output == input_part


def test_encode_gemini_part_with_image():
    """Test encode_gemini_part with a PIL image."""
    # Create a simple image
    image = PIL.Image.new("RGB", (10, 10), color="red")
    buffered = BytesIO()
    image.save(buffered, format="WEBP")
    img_bytes = buffered.getvalue()

    # Mock the image file
    mock_image = MagicMock(spec=PIL.WebPImagePlugin.WebPImageFile)
    mock_image.save = image.save

    output = encode_gemini_part(mock_image)
    assert output["mime_type"] == "image/webp"  # pyright: ignore [reportArgumentType]
    expected_data = base64.b64encode(img_bytes).decode("utf-8")
    assert output["data"] == expected_data  # pyright: ignore [reportArgumentType]


def test_serialize_proto_data_empty():
    """Test _serialize_proto_data with empty data."""
    data = []
    output = _serialize_proto_data(data)
    assert output == "[]"


def test_serialize_proto_data_without_parts():
    """Test _serialize_proto_data with data that has no 'parts' key."""
    data = [{"key": "value"}]
    output = _serialize_proto_data(data)
    assert output == json.dumps(data)


def test_serialize_proto_data_with_parts():
    """Test _serialize_proto_data with data containing 'parts'."""
    data = [
        {
            "key": "value",
            "parts": [
                "some string",
                {"mime_type": "application/octet-stream", "data": b"\x00\x01\x02"},
                {"key": "value"},
            ],
        }
    ]
    output = _serialize_proto_data(data)
    expected_data = [
        {
            "key": "value",
            "parts": [
                "some string",
                {
                    "mime_type": "application/octet-stream",
                    "data": base64.b64encode(b"\x00\x01\x02").decode("utf-8"),
                },
                {"key": "value"},
            ],
        }
    ]
    assert json.loads(output) == expected_data


def test_set_call_response_attributes_serializable():
    """Test _set_call_response_attributes with serializable data."""
    response = MagicMock()
    response.message_param = {"key": "value"}
    response.messages = [{"message": "hello"}]
    span = MagicMock()
    _set_call_response_attributes(response, span)
    expected_attributes = {
        "lilypad.generation.output": json.dumps(response.message_param),
        "lilypad.generation.messages": json.dumps(response.messages),
    }
    span.set_attributes.assert_called_once_with(expected_attributes)


def test_set_call_response_attributes_non_serializable_message_param():
    """Test _set_call_response_attributes with non-serializable message_param."""

    class NonSerializableObject:
        def __str__(self):
            return "NonSerializableObject"

    response = MagicMock()
    response.message_param = {"key": "value"}
    response.messages = [{"message": "hello"}]
    span = MagicMock()

    _set_call_response_attributes(response, span)

    expected_attributes = {
        "lilypad.generation.output": json.dumps(response.message_param),
        "lilypad.generation.messages": json.dumps(response.messages),
    }
    span.set_attributes.assert_called_once_with(expected_attributes)


def test_set_response_model_attributes_base_model_with_messages():
    """Test _set_response_model_attributes with BaseModel having messages."""
    result = MagicMock(spec=BaseModel)
    result.model_dump_json.return_value = '{"key": "value"}'
    result._response = MagicMock()
    result._response.messages = [{"message": "hello"}]
    span = MagicMock()
    _set_response_model_attributes(result, span)
    expected_attributes = {
        "lilypad.generation.output": '{"key": "value"}',
        "lilypad.generation.messages": '[{"message": "hello"}]',
    }
    span.set_attributes.assert_called_once_with(expected_attributes)


def test_set_response_model_attributes_base_type():
    """Test _set_response_model_attributes with BaseType."""
    result = "some value"
    span = MagicMock()
    _set_response_model_attributes(result, span)
    expected_attributes = {
        "lilypad.generation.output": "some value",
    }
    span.set_attributes.assert_called_once_with(expected_attributes)


def test_set_response_model_attributes_non_serializable():
    """Test _set_response_model_attributes with non-serializable data."""
    result = {"key": "value"}
    span = MagicMock()
    _set_response_model_attributes(result, span)
    expected_attributes = {
        "lilypad.generation.output": str(result),
    }
    span.set_attributes.assert_called_once_with(expected_attributes)


def test_handle_call_response_with_span():
    """Test _handle_call_response when span is provided."""
    result = MagicMock()
    fn = MagicMock()
    span = MagicMock()
    with patch(
        "lilypad._utils.middleware._set_call_response_attributes"
    ) as mock_set_attrs:
        _handle_call_response(result, fn, span)
        mock_set_attrs.assert_called_once_with(result, span)


def test_handle_call_response_without_span():
    """Test _handle_call_response when span is None."""
    result = MagicMock()
    fn = MagicMock()
    span = None
    with patch(
        "lilypad._utils.middleware._set_call_response_attributes"
    ) as mock_set_attrs:
        _handle_call_response(result, fn, span)
        mock_set_attrs.assert_not_called()


def test_handle_stream_with_span():
    """Test _handle_stream when span is provided."""
    stream = MagicMock()
    fn = MagicMock()
    span = MagicMock()
    call_response = MagicMock()
    stream.construct_call_response.return_value = call_response
    with patch(
        "lilypad._utils.middleware._set_call_response_attributes"
    ) as mock_set_attrs:
        _handle_stream(stream, fn, span)
        mock_set_attrs.assert_called_once_with(call_response, span)


def test_handle_stream_without_span():
    """Test _handle_stream when span is None."""
    stream = MagicMock()
    fn = MagicMock()
    span = None
    with patch(
        "lilypad._utils.middleware._set_call_response_attributes"
    ) as mock_set_attrs:
        _handle_stream(stream, fn, span)
        mock_set_attrs.assert_not_called()


def test_handle_response_model_with_span():
    """Test _handle_response_model when span is provided."""
    result = MagicMock()
    fn = MagicMock()
    span = MagicMock()
    with patch(
        "lilypad._utils.middleware._set_response_model_attributes"
    ) as mock_set_attrs:
        _handle_response_model(result, fn, span)
        mock_set_attrs.assert_called_once_with(result, span)


def test_handle_response_model_without_span():
    """Test _handle_response_model when span is None."""
    result = MagicMock()
    fn = MagicMock()
    span = None
    with patch(
        "lilypad._utils.middleware._set_response_model_attributes"
    ) as mock_set_attrs:
        _handle_response_model(result, fn, span)
        mock_set_attrs.assert_not_called()


def test_handle_structured_stream_with_span():
    """Test _handle_structured_stream when span is provided."""
    result = MagicMock()
    result.constructed_response_model = MagicMock()
    fn = MagicMock()
    span = MagicMock()
    with patch(
        "lilypad._utils.middleware._set_response_model_attributes"
    ) as mock_set_attrs:
        _handle_structured_stream(result, fn, span)
        mock_set_attrs.assert_called_once_with(result.constructed_response_model, span)


def test_handle_structured_stream_without_span():
    """Test _handle_structured_stream when span is None."""
    result = MagicMock()
    fn = MagicMock()
    span = None
    with patch(
        "lilypad._utils.middleware._set_response_model_attributes"
    ) as mock_set_attrs:
        _handle_structured_stream(result, fn, span)
        mock_set_attrs.assert_not_called()


@pytest.mark.asyncio
async def test_handle_call_response_async_with_span():
    """Test _handle_call_response_async when span is provided."""
    result = MagicMock()
    fn = MagicMock()
    span = MagicMock()
    with patch(
        "lilypad._utils.middleware._set_call_response_attributes"
    ) as mock_set_attrs:
        await _handle_call_response_async(result, fn, span)
        mock_set_attrs.assert_called_once_with(result, span)


@pytest.mark.asyncio
async def test_handle_call_response_async_without_span():
    """Test _handle_call_response_async when span is None."""
    result = MagicMock()
    fn = MagicMock()
    span = None
    with patch(
        "lilypad._utils.middleware._set_call_response_attributes"
    ) as mock_set_attrs:
        await _handle_call_response_async(result, fn, span)
        mock_set_attrs.assert_not_called()


@pytest.mark.asyncio
async def test_handle_stream_async_with_span():
    """Test _handle_stream_async when span is provided."""
    stream = MagicMock()
    fn = MagicMock()
    span = MagicMock()
    call_response = MagicMock()
    stream.construct_call_response.return_value = call_response
    with patch(
        "lilypad._utils.middleware._set_call_response_attributes"
    ) as mock_set_attrs:
        await _handle_stream_async(stream, fn, span)
        mock_set_attrs.assert_called_once_with(call_response, span)


@pytest.mark.asyncio
async def test_handle_stream_async_without_span():
    """Test _handle_stream_async when span is None."""
    stream = MagicMock()
    fn = MagicMock()
    span = None
    with patch(
        "lilypad._utils.middleware._set_call_response_attributes"
    ) as mock_set_attrs:
        await _handle_stream_async(stream, fn, span)
        mock_set_attrs.assert_not_called()


@pytest.mark.asyncio
async def test_handle_response_model_async_with_span():
    """Test _handle_response_model_async when span is provided."""
    result = MagicMock()
    fn = MagicMock()
    span = MagicMock()
    with patch(
        "lilypad._utils.middleware._set_response_model_attributes"
    ) as mock_set_attrs:
        await _handle_response_model_async(result, fn, span)
        mock_set_attrs.assert_called_once_with(result, span)


@pytest.mark.asyncio
async def test_handle_response_model_async_without_span():
    """Test _handle_response_model_async when span is None."""
    result = MagicMock()
    fn = MagicMock()
    span = None
    with patch(
        "lilypad._utils.middleware._set_response_model_attributes"
    ) as mock_set_attrs:
        await _handle_response_model_async(result, fn, span)
        mock_set_attrs.assert_not_called()


@pytest.mark.asyncio
async def test_handle_structured_stream_async_with_span():
    """Test _handle_structured_stream_async when span is provided."""
    result = MagicMock()
    result.constructed_response_model = MagicMock()
    fn = MagicMock()
    span = MagicMock()
    with patch(
        "lilypad._utils.middleware._set_response_model_attributes"
    ) as mock_set_attrs:
        await _handle_structured_stream_async(result, fn, span)
        mock_set_attrs.assert_called_once_with(result.constructed_response_model, span)


@pytest.mark.asyncio
async def test_handle_structured_stream_async_without_span():
    """Test _handle_structured_stream_async when span is None."""
    result = MagicMock()
    fn = MagicMock()
    span = None
    with patch(
        "lilypad._utils.middleware._set_response_model_attributes"
    ) as mock_set_attrs:
        await _handle_structured_stream_async(result, fn, span)
        mock_set_attrs.assert_not_called()


def test_get_custom_context_manager():
    """Test _get_custom_context_manager function."""
    generation = MagicMock()
    generation.uuid = UUID("123e4567-e89b-12d3-a456-426614174123")
    generation.signature = "def fn(): pass"
    generation.code = "def fn(): pass"
    generation.version_num = 1
    generation.arg_types = {"arg1": "type1"}
    generation.arg_values = {"arg1": "value1"}
    is_async = False
    prompt_template = "prompt template"
    fn = MagicMock()
    fn.__name__ = "fn"

    tracer = MagicMock()
    span = MagicMock()
    tracer.start_as_current_span.return_value.__enter__.return_value = span
    project_uuid = UUID("123e4567-e89b-12d3-a456-426614174000")
    with patch("lilypad._utils.middleware.get_tracer", return_value=tracer):
        arg_values = {"param": "value"}
        context_manager_factory = _get_custom_context_manager(
            generation, arg_values, is_async, prompt_template, project_uuid
        )
        with context_manager_factory(fn) as cm_span:
            assert cm_span == span
            expected_attributes = {
                "lilypad.project_uuid": str(project_uuid),
                "lilypad.type": "generation",
                "lilypad.generation.uuid": str(generation.uuid),
                "lilypad.generation.name": fn.__name__,
                "lilypad.generation.signature": generation.signature,
                "lilypad.generation.code": generation.code,
                "lilypad.generation.arg_types": json.dumps(generation.arg_types),
                "lilypad.generation.arg_values": json.dumps(arg_values),
                "lilypad.generation.prompt_template": prompt_template,
                "lilypad.generation.version": 1,
                "lilypad.is_async": is_async,
            }
            span.set_attributes.assert_called_once_with(expected_attributes)


def test_create_mirascope_middleware():
    """Test create_mirascope_middleware function."""
    version = MagicMock()
    is_async = False
    prompt_template = None

    with (
        patch(
            "lilypad._utils.middleware.middleware_factory"
        ) as mock_middleware_factory,
        patch("lilypad._utils.middleware._get_custom_context_manager") as mock_get_cm,
    ):
        mock_get_cm.return_value = "custom_context_manager"

        middleware = create_mirascope_middleware(version, {}, is_async, prompt_template)

        mock_middleware_factory.assert_called_once_with(
            custom_context_manager="custom_context_manager",
            handle_call_response=_handle_call_response,
            handle_call_response_async=_handle_call_response_async,
            handle_stream=_handle_stream,
            handle_stream_async=_handle_stream_async,
            handle_response_model=_handle_response_model,
            handle_response_model_async=_handle_response_model_async,
            handle_structured_stream=_handle_structured_stream,
            handle_structured_stream_async=_handle_structured_stream_async,
        )
        assert middleware == mock_middleware_factory.return_value
