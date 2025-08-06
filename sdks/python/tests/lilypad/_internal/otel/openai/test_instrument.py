"""Tests for OpenAI instrumentation."""

import inspect

from openai import OpenAI, AsyncOpenAI

from lilypad._internal.otel.openai.instrument import instrument_openai


def test_sync_client_methods_are_patched():
    """Test that OpenAI sync client methods are patched while maintaining signatures."""
    client = OpenAI(api_key="test")
    original_create = client.chat.completions.create
    original_parse = client.chat.completions.parse

    original_create_sig = inspect.signature(original_create)
    original_parse_sig = inspect.signature(original_parse)

    instrument_openai(client)

    assert client.chat.completions.create is not original_create
    assert client.chat.completions.parse is not original_parse

    assert inspect.signature(client.chat.completions.create) == original_create_sig
    assert inspect.signature(client.chat.completions.parse) == original_parse_sig


def test_async_client_methods_are_patched():
    """Test that AsyncOpenAI client methods are patched while maintaining signatures."""
    client = AsyncOpenAI(api_key="test")
    original_create = client.chat.completions.create
    original_parse = client.chat.completions.parse

    original_create_sig = inspect.signature(original_create)
    original_parse_sig = inspect.signature(original_parse)

    instrument_openai(client)

    assert client.chat.completions.create is not original_create
    assert client.chat.completions.parse is not original_parse

    assert inspect.signature(client.chat.completions.create) == original_create_sig
    assert inspect.signature(client.chat.completions.parse) == original_parse_sig


def test_patched_methods_are_callable():
    """Test that patched methods remain callable."""
    client = OpenAI(api_key="test")
    instrument_openai(client)

    assert callable(client.chat.completions.create)
    assert callable(client.chat.completions.parse)


def test_patched_methods_have_wrapped_attribute():
    """Test that patched methods have __wrapped__ attribute for introspection."""
    client = OpenAI(api_key="test")

    instrument_openai(client)

    assert hasattr(client.chat.completions.create, "__wrapped__")
    assert hasattr(client.chat.completions.parse, "__wrapped__")
    assert callable(client.chat.completions.create.__wrapped__)  # pyright: ignore[reportAttributeAccessIssue]
    assert callable(client.chat.completions.parse.__wrapped__)  # pyright: ignore[reportAttributeAccessIssue]


def test_client_marked_as_instrumented():
    """Test that client is marked as instrumented after instrumentation."""
    client = OpenAI(api_key="test")

    assert not hasattr(client, "_lilypad_instrumented")

    instrument_openai(client)

    assert hasattr(client, "_lilypad_instrumented")
    assert client._lilypad_instrumented is True  # pyright: ignore[reportAttributeAccessIssue]


def test_instrumentation_idempotent():
    """Test that instrumentation is truly idempotent."""
    client = OpenAI(api_key="test")

    instrument_openai(client)
    first_create = client.chat.completions.create
    first_parse = client.chat.completions.parse

    instrument_openai(client)
    second_create = client.chat.completions.create
    second_parse = client.chat.completions.parse

    assert second_create is first_create
    assert second_parse is first_parse


def test_async_instrumentation_idempotent():
    """Test that async instrumentation is truly idempotent."""
    client = AsyncOpenAI(api_key="test")

    instrument_openai(client)
    first_create = client.chat.completions.create
    first_parse = client.chat.completions.parse

    instrument_openai(client)
    second_create = client.chat.completions.create
    second_parse = client.chat.completions.parse

    assert second_create is first_create
    assert second_parse is first_parse


def test_preserves_async_nature():
    """Test that async methods remain async after patching."""
    from pydantic import BaseModel

    class TestResponse(BaseModel):
        test: str

    client = AsyncOpenAI(api_key="test")

    create_result_before = client.chat.completions.create(model="test", messages=[])
    parse_result_before = client.chat.completions.parse(
        model="test", messages=[], response_format=TestResponse
    )
    assert inspect.iscoroutine(create_result_before)
    assert inspect.iscoroutine(parse_result_before)
    create_result_before.close()
    parse_result_before.close()

    instrument_openai(client)

    create_result_after = client.chat.completions.create(model="test", messages=[])
    parse_result_after = client.chat.completions.parse(
        model="test", messages=[], response_format=TestResponse
    )
    assert inspect.iscoroutine(create_result_after)
    assert inspect.iscoroutine(parse_result_after)
    create_result_after.close()
    parse_result_after.close()
