"""Project model"""

import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from lilypad.server.models import BaseSQLModel

from .table_names import PROJECT_TABLE_NAME

if TYPE_CHECKING:
    from lilypad.server.models import LLMFunctionTable


class ProjectBase(BaseSQLModel):
    """Project model"""

    name: str = Field(nullable=False, unique=True)


class ProjectTable(ProjectBase, table=True):
    """Project model"""

    __tablename__ = PROJECT_TABLE_NAME  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    llm_fns: list["LLMFunctionTable"] = Relationship(back_populates="project")
