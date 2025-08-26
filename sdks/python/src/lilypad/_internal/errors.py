"""Custom error classes for Lilypad SDK."""

from typing import Any

from .._generated.core.api_error import ApiError


class NotFoundError(ApiError):
    """Error raised when a resource is not found (404)."""

    def __init__(
        self,
        body: Any | None,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(status_code=404, headers=headers, body=body)
