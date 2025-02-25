"""Projects schemas."""

from datetime import datetime
from uuid import UUID

from ..models.projects import _ProjectBase
from .generations import GenerationPublic
from .response_models import ResponseModelPublic


class ProjectCreate(_ProjectBase):
    """Project Create Model."""

    ...


class ProjectPublic(_ProjectBase):
    """Project Public Model."""

    uuid: UUID
    generations: list[GenerationPublic] = []
    response_models: list[ResponseModelPublic] = []
    created_at: datetime
