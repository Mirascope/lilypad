"""Public exception classes for Lilypad SDK."""

from __future__ import annotations


class LilypadException(Exception):
    """Base exception for all Lilypad SDK errors."""

    pass


class SpanNotFoundError(LilypadException):
    """Raised when attempting to access a span that doesn't exist."""

    pass


class RemoteExecutionError(LilypadException):
    """Raised when remote execution of a function fails."""

    pass


class VersionResolutionError(LilypadException):
    """Raised when a version reference cannot be resolved."""

    pass


class ConfigurationError(LilypadException):
    """Raised when SDK configuration is invalid or missing required settings."""

    pass
