"""Lilypad exceptions"""

from typing import Literal

from httpx import HTTPError, RequestError, TimeoutException


class LilypadException(Exception):
    """Base class for all Lilypad exceptions."""


class LicenseError(LilypadException):
    """Custom exception for license-related errors"""


class RemoteFunctionError(LilypadException):
    """Raised when a remote function call fails."""


class LilypadNotFoundError(LilypadException):
    """Raised when an API response has a status code of 404."""

    status_code: Literal[404] = 404


class LilypadRateLimitError(LilypadException):
    """Raised when an API response has a status code of 429."""

    status_code: Literal[429] = 429


class LilypadAPIConnectionError(LilypadException):
    """Raised when an API connection error occurs."""


class LilypadValueError(LilypadException):
    """Inappropriate argument value (of correct type)."""


class LilypadFileNotFoundError(LilypadException):
    """Raised when a file or directory is requested but doesn't exist."""


class LilypadHTTPError(LilypadException, HTTPError):
    """An HTTP error occurred."""


class LilypadRequestException(LilypadException, RequestError):
    """There was an ambiguous exception that occurred while handling your request."""


class LilypadTimeout(LilypadException, TimeoutException):
    """The request timed out."""


class LilypadPaymentRequiredError(LilypadException):
    """Raised when an API response has a status code of 402."""

    status_code: Literal[402] = 402


class SpanNotFoundError(LilypadException):
    """Raised when a span cannot be found."""
