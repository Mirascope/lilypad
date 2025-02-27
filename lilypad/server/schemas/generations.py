"""Generations schemas."""

from uuid import UUID

from ..models.generations import _GenerationBase


class GenerationCreate(_GenerationBase):
    """Generation create model."""


class GenerationPublic(_GenerationBase):
    """Generation public model."""

    uuid: UUID
