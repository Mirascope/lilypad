"""Projects schemas."""

from datetime import datetime
from uuid import UUID

from ..models.projects import _ProjectBase
from .functions import FunctionPublic


class ProjectCreate(_ProjectBase):
    """Project Create Model."""

    ...


class ProjectPublic(_ProjectBase):
    """Project Public Model."""

    uuid: UUID
    functions: list[FunctionPublic] = []
    created_at: datetime
