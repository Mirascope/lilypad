"""Tests for lilypad._utils.call_safely module."""

import logging
import pytest

from lilypad.exceptions import LilypadException
from lilypad.generated.core.api_error import ApiError
from lilypad._utils.call_safely import call_safely, _default_logger


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


def test_call_safely_with_exclude() -> None:
    """Test call_safely decorator with exclude parameter (line 91)."""

    def fallback() -> str:
        return "fallback"

    # Test with ApiError being excluded
    @call_safely(fallback, exclude=(ApiError,))
    def api_error_excluded() -> str:
        raise ApiError(status_code=404, body="Not found", headers={})

    # ApiError should be re-raised because it's in exclude list
    with pytest.raises(ApiError):
        api_error_excluded()

    # Test with LilypadException being excluded
    @call_safely(fallback, exclude=(LilypadException,))
    def lilypad_error_excluded() -> str:
        raise LilypadException("This should be re-raised")

    # LilypadException should be re-raised because it's in exclude list
    with pytest.raises(LilypadException, match="This should be re-raised"):
        lilypad_error_excluded()

    @call_safely(fallback, exclude=(ApiError,))
    def error_not_excluded() -> str:
        raise LilypadException("This should trigger fallback")

    # LilypadException should trigger fallback since it's not excluded
    assert error_not_excluded() == "fallback"


@pytest.mark.asyncio
async def test_call_safely_async_with_exclude() -> None:
    """Test call_safely decorator with exclude parameter for async functions (line 69)."""

    async def fallback() -> str:
        return "async fallback"

    # Test with ApiError being excluded
    @call_safely(fallback, exclude=(ApiError,))
    async def async_api_error_excluded() -> str:
        raise ApiError(status_code=500, body="Server error", headers={})

    # ApiError should be re-raised because it's in exclude list
    with pytest.raises(ApiError):
        await async_api_error_excluded()

    # Test with LilypadException being excluded
    @call_safely(fallback, exclude=(LilypadException,))
    async def async_lilypad_error_excluded() -> str:
        raise LilypadException("This should be re-raised async")

    # LilypadException should be re-raised because it's in exclude list
    with pytest.raises(LilypadException, match="This should be re-raised async"):
        await async_lilypad_error_excluded()

    @call_safely(fallback, exclude=(ApiError,))
    async def async_error_not_excluded() -> str:
        raise LilypadException("This should trigger async fallback")

    # LilypadException should trigger fallback since it's not excluded
    assert await async_error_not_excluded() == "async fallback"


def test_default_logger() -> None:
    """Test _default_logger function creates logger with handler when none exists."""
    # Create a logger without handlers to trigger the setup code
    test_logger_name = "test_lilypad_logger"

    # Clear any existing handlers
    logger = logging.getLogger(test_logger_name)
    logger.handlers.clear()

    # Call _default_logger which should add handler
    result_logger = _default_logger(test_logger_name)

    # Verify logger has handler now
    assert len(result_logger.handlers) == 1
    assert isinstance(result_logger.handlers[0], logging.StreamHandler)
    assert result_logger.level == logging.INFO

    # Verify formatter is set
    formatter = result_logger.handlers[0].formatter
    assert formatter is not None
    assert "%(asctime)s" in formatter._fmt
    assert "%(name)s" in formatter._fmt
    assert "%(levelname)s" in formatter._fmt
    assert "%(message)s" in formatter._fmt

    # Clean up
    logger.handlers.clear()
