"""Project model"""

import datetime

from sqlmodel import Field

from lilypad.app.schemas.project import ProjectCreate

from .table_names import PROJECT_TABLE_TABLE


class ProjectTable(ProjectCreate, table=True):
    """Project model"""

    __tablename__ = PROJECT_TABLE_TABLE  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime.datetime = Field(
        default=datetime.datetime.now(datetime.UTC), nullable=False
    )
