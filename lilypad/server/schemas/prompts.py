"""Prompts schemas."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel

from ..models.prompts import Provider, _PromptBase


class PromptPublic(_PromptBase):
    """Prompt public model."""

    uuid: UUID


class PromptCreate(_PromptBase):
    """Prompt create model."""


class PlaygroundParameters(BaseModel):
    """Playground parameters model."""

    arg_values: dict[str, Any]
    provider: Provider
    model: str
    prompt: PromptCreate | None = None
