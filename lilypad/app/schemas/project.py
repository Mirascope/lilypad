"""Project schema"""

from sqlmodel import Field

from .base_sql_model import BaseSQLModel


class ProjectCreate(BaseSQLModel):
    """project schema"""

    name: str = Field(nullable=False, unique=True)
