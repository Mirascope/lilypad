"""Lilypad exceptions"""

from typing import Literal


class LilypadException(Exception):
    """Base class for all Lilypad exceptions."""


class LilypadNotFoundError(LilypadException):
    """Raised when an API response has a status code of 404."""

    status_code: Literal[404] = 404


class LilypadAPIConnectionError(LilypadException):
    """Raised when an API connection error occurs."""

    ...
