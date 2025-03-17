"""Generations schemas."""

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, TypeAdapter, field_validator

from ..models.generations import _GenerationBase


class Provider(str, Enum):
    """Provider name enum"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    GEMINI = "gemini"


class GenerationCreate(_GenerationBase):
    """Generation create model."""


class GenerationPublic(_GenerationBase):
    """Generation public model."""

    uuid: UUID


AcceptedValue = int | float | bool | str | list | dict[str, Any]


accepted_value_adapter = TypeAdapter(AcceptedValue)


class PlaygroundParameters(BaseModel):
    """Playground parameters model."""

    arg_values: dict[str, AcceptedValue]
    provider: Provider
    model: str
    generation: GenerationCreate | None = None

    @field_validator("arg_values")
    def check_nested_values(cls, values: Any) -> None:
        """arg_values is a dictionary of key-value pairs where the value can be"""
        if not isinstance(values, dict | list):
            return values
        return accepted_value_adapter.validate_python(values)
