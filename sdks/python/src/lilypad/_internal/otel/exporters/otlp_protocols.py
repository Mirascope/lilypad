"""Protocol definitions for OTLP type safety.

This module defines protocols for stricter type checking without using Any.
"""

from collections.abc import Sequence
from typing import Protocol, TypeAlias, TypeVar

# Define strict attribute value types
# Align with OpenTelemetry's AttributeValue type which includes Sequences
PrimitiveValue: TypeAlias = bool | int | float | str
AttributeValueType: TypeAlias = (
    str
    | bool
    | int
    | float
    | Sequence[str]
    | Sequence[bool]
    | Sequence[int]
    | Sequence[float]
)

# Generic type for attribute value conversion
T = TypeVar("T", bound="AttributeValueProtocol")


class AttributeValueProtocol(Protocol):
    """Protocol for OTLP attribute values."""

    bool_value: bool | None
    int_value: str | None
    double_value: float | None
    string_value: str | None
