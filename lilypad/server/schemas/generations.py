"""Generations schemas."""

from uuid import UUID

from ..models.generations import _GenerationBase
from .prompts import PromptPublic
from .response_models import ResponseModelPublic


class GenerationCreate(_GenerationBase):
    """Generation create model."""


class GenerationPublic(_GenerationBase):
    """Generation public model."""

    uuid: UUID
    prompt: PromptPublic | None = None
    response_model: ResponseModelPublic | None = None
