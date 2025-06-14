"""Test cases for Lilypad exceptions."""

import pytest
from httpx import HTTPError, RequestError, TimeoutException

from lilypad.exceptions import (
    LilypadException,
    LicenseError,
    RemoteFunctionError,
    LilypadNotFoundError,
    LilypadRateLimitError,
    LilypadAPIConnectionError,
    LilypadValueError,
    LilypadFileNotFoundError,
    LilypadHTTPError,
    LilypadRequestException,
    LilypadTimeout,
    LilypadPaymentRequiredError,
    SpanNotFoundError,
)


def test_lilypad_exception_inheritance():
    """Test that all custom exceptions inherit from LilypadException."""
    assert issubclass(LicenseError, LilypadException)
    assert issubclass(RemoteFunctionError, LilypadException)
    assert issubclass(LilypadNotFoundError, LilypadException)
    assert issubclass(LilypadRateLimitError, LilypadException)
    assert issubclass(LilypadAPIConnectionError, LilypadException)
    assert issubclass(LilypadValueError, LilypadException)
    assert issubclass(LilypadFileNotFoundError, LilypadException)
    assert issubclass(LilypadHTTPError, LilypadException)
    assert issubclass(LilypadRequestException, LilypadException)
    assert issubclass(LilypadTimeout, LilypadException)
    assert issubclass(LilypadPaymentRequiredError, LilypadException)
    assert issubclass(SpanNotFoundError, LilypadException)


def test_lilypad_exception_instantiation():
    """Test that all exceptions can be instantiated with a message."""
    message = "Test error message"

    exc = LilypadException(message)
    assert str(exc) == message

    exc = LicenseError(message)
    assert str(exc) == message

    exc = RemoteFunctionError(message)
    assert str(exc) == message

    exc = LilypadAPIConnectionError(message)
    assert str(exc) == message

    exc = LilypadValueError(message)
    assert str(exc) == message

    exc = LilypadFileNotFoundError(message)
    assert str(exc) == message

    exc = SpanNotFoundError(message)
    assert str(exc) == message


def test_status_code_exceptions():
    """Test exceptions with specific status codes."""
    # Test LilypadNotFoundError
    exc = LilypadNotFoundError("Not found")
    assert exc.status_code == 404
    assert isinstance(exc.status_code, int)

    # Test LilypadRateLimitError
    exc = LilypadRateLimitError("Rate limited")
    assert exc.status_code == 429
    assert isinstance(exc.status_code, int)

    # Test LilypadPaymentRequiredError
    exc = LilypadPaymentRequiredError("Payment required")
    assert exc.status_code == 402
    assert isinstance(exc.status_code, int)


def test_httpx_inheritance():
    """Test that HTTP-related exceptions inherit from httpx exceptions."""
    # Test LilypadHTTPError
    assert issubclass(LilypadHTTPError, HTTPError)
    assert issubclass(LilypadHTTPError, LilypadException)

    # Test LilypadRequestException
    assert issubclass(LilypadRequestException, RequestError)
    assert issubclass(LilypadRequestException, LilypadException)

    # Test LilypadTimeout
    assert issubclass(LilypadTimeout, TimeoutException)
    assert issubclass(LilypadTimeout, LilypadException)


def test_exception_raising():
    """Test raising and catching custom exceptions."""
    # Test raising and catching LilypadException
    with pytest.raises(LilypadException) as exc_info:
        raise LilypadException("Base exception")
    assert str(exc_info.value) == "Base exception"

    # Test raising and catching specific exceptions
    with pytest.raises(LicenseError) as exc_info:
        raise LicenseError("Invalid license")
    assert str(exc_info.value) == "Invalid license"

    with pytest.raises(RemoteFunctionError) as exc_info:
        raise RemoteFunctionError("Remote function failed")
    assert str(exc_info.value) == "Remote function failed"

    # Test that specific exceptions can be caught as LilypadException
    with pytest.raises(LilypadException):
        raise LicenseError("Should be caught as LilypadException")


def test_exception_hierarchy():
    """Test the exception hierarchy works correctly."""

    # Create a function that raises different exceptions
    def raise_exception(exc_type, message="Test"):
        raise exc_type(message)

    # Test catching specific exception
    try:
        raise_exception(LilypadNotFoundError)
    except LilypadNotFoundError as e:
        assert e.status_code == 404
    except LilypadException:
        pytest.fail("Should have caught LilypadNotFoundError specifically")

    # Test catching base exception
    try:
        raise_exception(SpanNotFoundError)
    except LilypadException as e:
        assert isinstance(e, SpanNotFoundError)
    except Exception:
        pytest.fail("Should have caught as LilypadException")
