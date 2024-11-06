"""Project Models."""

from pydantic import BaseModel

from lilypad.models.llm_fns import LLMFunctionPublic
from lilypad.server.models import ProjectBase


class ProjectPublic(ProjectBase):
    """Project public model"""

    id: int
    llm_fns: list[LLMFunctionPublic] = []


class ProjectCreate(BaseModel):
    """Project create model"""

    name: str
