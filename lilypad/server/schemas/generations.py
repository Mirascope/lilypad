"""Generations schemas."""

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel

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


class PlaygroundParameters(BaseModel):
    """Playground parameters model."""

    arg_values: dict[str, Any]
    provider: Provider
    model: str
    generation: GenerationCreate | None = None
