"""Project model"""

import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from lilypad.server.models import BaseSQLModel

from .table_names import PROJECT_TABLE_NAME, PROMPT_VERSION_TABLE_NAME

if TYPE_CHECKING:
    from lilypad.server.models import CallTable, ProjectTable


class PromptVersionTable(BaseSQLModel, table=True):
    """Prompt version model"""

    __tablename__ = PROMPT_VERSION_TABLE_NAME  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(default=None, foreign_key=f"{PROJECT_TABLE_NAME}.id")
    prompt_template: str = Field(nullable=False)
    created_at: datetime.datetime = Field(
        default=datetime.datetime.now(datetime.UTC), nullable=False
    )
    previous_version_id: int | None = Field(
        default=None, foreign_key=f"{PROMPT_VERSION_TABLE_NAME}.id"
    )

    project: "ProjectTable" = Relationship(back_populates="prompt_versions")
    calls: list["CallTable"] = Relationship(
        back_populates="prompt_version", cascade_delete=True
    )
