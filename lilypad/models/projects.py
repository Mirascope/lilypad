"""Project Models."""

from pydantic import BaseModel

from lilypad.server.models import ProjectBase


class ProjectPublic(ProjectBase):
    """Project public model"""

    id: int


class ProjectCreate(BaseModel):
    """Project create model"""

    name: str
