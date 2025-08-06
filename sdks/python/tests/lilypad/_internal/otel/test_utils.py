from unittest.mock import Mock

import httpx
from lilypad._internal.otel.utils import (
    ChoiceBuffer,
    ToolCallBuffer,
    set_server_address_and_port,
)


def test_choice_buffer_init():
    buffer = ChoiceBuffer(0)
    assert buffer.index == 0
    assert buffer.finish_reason is None
    assert buffer.text_content == []
    assert buffer.tool_calls_buffers == []


def test_append_text_content():
    buffer = ChoiceBuffer(0)
    buffer.append_text_content("Hello")
    buffer.append_text_content(" World")

    assert buffer.text_content == ["Hello", " World"]


def test_append_tool_call():
    buffer = ChoiceBuffer(0)

    tool_call = Mock()
    tool_call.index = 0
    tool_call.id = "call_123"
    tool_call.function = Mock()
    tool_call.function.name = "test_func"
    tool_call.function.arguments = '{"arg": "value"}'

    buffer.append_tool_call(tool_call)

    assert len(buffer.tool_calls_buffers) == 1
    assert buffer.tool_calls_buffers[0] is not None
    assert buffer.tool_calls_buffers[0].tool_call_id == "call_123"
    assert buffer.tool_calls_buffers[0].function_name == "test_func"


def test_append_multiple_tool_calls():
    buffer = ChoiceBuffer(0)

    tool_call1 = Mock(index=0, id="call_1")
    tool_call1.function = Mock(name="func1", arguments='{"a": 1}')
    tool_call2 = Mock(index=1, id="call_2")
    tool_call2.function = Mock(name="func2", arguments='{"b": 2}')
    tool_call3 = Mock(index=0, id="call_1")
    tool_call3.function = Mock(name="func1", arguments='{"c": 3}')

    buffer.append_tool_call(tool_call1)
    buffer.append_tool_call(tool_call2)
    buffer.append_tool_call(tool_call3)

    assert len(buffer.tool_calls_buffers) == 2
    assert buffer.tool_calls_buffers[0] is not None
    assert buffer.tool_calls_buffers[0].arguments == ['{"a": 1}', '{"c": 3}']
    assert buffer.tool_calls_buffers[1] is not None
    assert buffer.tool_calls_buffers[1].arguments == ['{"b": 2}']


def test_tool_call_buffer_init():
    buffer = ToolCallBuffer(0, "call_123", "test_func")

    assert buffer.index == 0
    assert buffer.tool_call_id == "call_123"
    assert buffer.function_name == "test_func"
    assert buffer.arguments == []


def test_append_arguments():
    buffer = ToolCallBuffer(0, "call_123", "test_func")

    buffer.append_arguments('{"part1": ')
    buffer.append_arguments('"value",')
    buffer.append_arguments(' "part2": "value2"}')

    assert buffer.arguments == ['{"part1": ', '"value",', ' "part2": "value2"}']


def test_set_server_address_from_base_url():
    attributes = {}
    client_instance = Mock()
    client_instance._client = httpx.Client(base_url="https://api.openai.com:443")

    set_server_address_and_port(client_instance, attributes)

    assert attributes["server.address"] == "api.openai.com"
    assert "server.port" not in attributes


def test_set_server_address_from_url_string():
    attributes = {}
    client_instance = Mock()
    client_instance._client = httpx.Client(base_url="https://api.example.com:8080")

    set_server_address_and_port(client_instance, attributes)

    assert attributes["server.address"] == "api.example.com"
    assert attributes["server.port"] == 8080


def test_set_server_address_no_port():
    attributes = {}
    client_instance = Mock()
    client_instance._client = httpx.Client(base_url="https://api.example.com")

    set_server_address_and_port(client_instance, attributes)

    assert attributes["server.address"] == "api.example.com"
    assert "server.port" not in attributes


def test_set_server_address_http():
    attributes = {}
    client_instance = Mock()
    client_instance._client = httpx.Client(base_url="http://localhost:8080")

    set_server_address_and_port(client_instance, attributes)

    assert attributes["server.address"] == "localhost"
    assert attributes["server.port"] == 8080


def test_set_server_address_no_base_url():
    attributes = {}
    client_instance = Mock()
    client_instance._client = Mock()
    client_instance._client.base_url = None

    set_server_address_and_port(client_instance, attributes)

    assert "server.address" not in attributes
    assert "server.port" not in attributes
