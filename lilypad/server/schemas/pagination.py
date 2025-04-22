from __future__ import annotations

from collections.abc import Sequence
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T_co = TypeVar("T_co", covariant=True)


class Paginated(BaseModel, Generic[T_co]):
    """A generic, read‑only pagination container."""

    items: Sequence[T_co] = Field(..., description="Current slice of items")
    limit: int = Field(..., ge=1, description="Requested page size (limit)")
    offset: int = Field(..., ge=0, description="Requested offset")
    total: int = Field(..., ge=0, description="Total number of items")


__all__ = ["Paginated"]
