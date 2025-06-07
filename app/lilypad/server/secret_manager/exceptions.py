"""Exceptions for secret manager operations."""


class SecretManagerError(Exception):
    """Base exception for secret manager errors."""

    pass


class SecretNotFoundError(SecretManagerError):
    """Raised when a secret is not found."""

    pass


class SecretAccessDeniedError(SecretManagerError):
    """Raised when access to a secret is denied."""

    pass


class SecretValidationError(SecretManagerError):
    """Raised when secret validation fails."""

    pass


class SecretOperationError(SecretManagerError):
    """Raised when a secret operation fails."""

    pass


class BinarySecretError(SecretManagerError):
    """Raised when a secret is in binary format and cannot be processed."""

    pass
