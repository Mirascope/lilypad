from __future__ import annotations

from collections.abc import Sequence
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T_co = TypeVar("T_co", covariant=True)


class Paginated(BaseModel, Generic[T_co]):
    """A generic, read‑only pagination container.

    Parameters
    ----------
    items:
        The resources in the current window.
    limit:
        The requested page size.  Guaranteed to be ``>= 1``.
    offset:
        The zero‑based offset of the first element of *items* relative to the
        complete collection.
    total:
        The total number of items available **before** pagination.  Allows
        clients to determine whether further pages are available without an
        additional round‑trip.
    """

    items: Sequence[T_co] = Field(..., description="Current slice of items")
    limit: int = Field(..., ge=1, description="Requested page size (limit)")
    offset: int = Field(..., ge=0, description="Requested offset")
    total: int = Field(..., ge=0, description="Total number of items")

    model_config = {
        "frozen": True,
        "json_schema_extra": {
            "examples": [
                {
                    "items": [],
                    "limit": 100,
                    "offset": 0,
                    "total": 0,
                }
            ]
        },
    }


__all__ = ["Paginated"]
