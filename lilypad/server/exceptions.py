"""Exceptions for the Lilypad server."""

from typing import Literal

from fastapi import HTTPException

from lilypad.exceptions import LilypadException


class LilypadServerError(LilypadException, HTTPException):
    """Base class for all Lilypad server exceptions."""

    def __init__(self, detail: str, status_code: int | None = None) -> None:
        super().__init__(status_code=status_code or self.status_code, detail=detail)


class LilypadForbiddenError(LilypadServerError):
    """Raise when request is Forbidden."""

    status_code: Literal[403] = 403
