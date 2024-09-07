"""Project model"""

import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from lilypad.app.models import BaseSQLModel

from .table_names import PROJECT_TABLE_NAME

if TYPE_CHECKING:
    from lilypad.app.models import PromptVersionTable


class ProjectTable(BaseSQLModel, table=True):
    """Project model"""

    __tablename__ = PROJECT_TABLE_NAME  # type: ignore

    id: int = Field(default=None, primary_key=True)
    name: str = Field(nullable=False, unique=True)
    created_at: datetime.datetime = Field(
        default=datetime.datetime.now(datetime.UTC), nullable=False
    )
    prompt_versions: list["PromptVersionTable"] = Relationship(
        back_populates="project", cascade_delete=True
    )
