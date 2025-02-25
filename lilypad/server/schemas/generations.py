"""Generations schemas."""

from uuid import UUID

from ..models.generations import _GenerationBase
from .response_models import ResponseModelPublic
from .tool import ToolPublic


class GenerationCreate(_GenerationBase):
    """Generation create model."""


class GenerationPublic(_GenerationBase):
    """Generation public model."""

    uuid: UUID
    response_model: ResponseModelPublic | None = None
    tools: list[ToolPublic] | None = None
