"""Projects schemas."""

from datetime import datetime
from uuid import UUID

from ..models.projects import _ProjectBase
from .generations import GenerationPublic


class ProjectCreate(_ProjectBase):
    """Project Create Model."""

    ...


class ProjectPublic(_ProjectBase):
    """Project Public Model."""

    uuid: UUID
    generations: list[GenerationPublic] = []
    created_at: datetime
