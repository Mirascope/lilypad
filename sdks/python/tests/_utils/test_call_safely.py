"""Tests for lilypad._utils.call_safely module."""

import pytest

from lilypad.lib.exceptions import LilypadException
from lilypad.lib._utils.call_safely import call_safely


def test_call_safely() -> None:
    """Test the `call_safely` decorator."""

    def fn() -> str:
        return "Hello, world!"

    @call_safely(fn)
    def error() -> str:
        raise LilypadException("Error")

    assert error() == "Hello, world!"

    @call_safely(fn)
    def no_error() -> str:
        return "No error"

    assert no_error() == "No error"

    @call_safely(fn)
    def user_error() -> str:
        raise ValueError("User error")

    with pytest.raises(ValueError):
        user_error()


@pytest.mark.asyncio
async def test_call_safely_async() -> None:
    """Test the `call_safely` decorator with async functions."""

    async def fn() -> str:
        return "Hello, world!"

    @call_safely(fn)
    async def error() -> str:
        raise LilypadException("Error")

    assert await error() == "Hello, world!"

    @call_safely(fn)
    async def no_error() -> str:
        return "No error"

    assert await no_error() == "No error"

    @call_safely(fn)
    async def user_error() -> str:
        raise ValueError("User error")

    with pytest.raises(ValueError):
        await user_error()
