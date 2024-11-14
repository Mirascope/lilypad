"""Versions table and models."""

from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship

from .base_sql_model import BaseSQLModel
from .functions import FunctionPublic
from .prompts import PromptPublic
from .spans import SpanPublic
from .table_names import (
    FUNCTION_TABLE_NAME,
    PROJECT_TABLE_NAME,
    PROMPT_TABLE_NAME,
    VERSION_TABLE_NAME,
)

if TYPE_CHECKING:
    from .functions import FunctionTable
    from .projects import ProjectTable
    from .prompts import PromptTable
    from .spans import SpanTable


class _VersionBase(BaseSQLModel):
    """Version base model"""

    version_num: int
    project_id: int | None = Field(default=None, foreign_key=f"{PROJECT_TABLE_NAME}.id")
    function_id: int | None = Field(
        default=None, foreign_key=f"{FUNCTION_TABLE_NAME}.id"
    )
    prompt_id: int | None = Field(default=None, foreign_key=f"{PROMPT_TABLE_NAME}.id")
    function_name: str = Field(nullable=False, index=True)
    function_hash: str = Field(nullable=False, index=True)
    prompt_hash: str | None = Field(default=None, index=True)
    is_active: bool = Field(default=False)


class VersionCreate(_VersionBase):
    """Version create model"""


class VersionPublic(_VersionBase):
    """Version public model"""

    id: int
    function: FunctionPublic
    prompt: PromptPublic | None
    spans: list[SpanPublic]


class ActiveVersionPublic(_VersionBase):
    """Active version public model"""

    id: int
    function: FunctionPublic
    prompt: PromptPublic
    spans: list[SpanPublic]


class VersionTable(_VersionBase, table=True):
    """Version table"""

    __tablename__ = VERSION_TABLE_NAME  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    project: "ProjectTable" = Relationship(back_populates="versions")
    function: "FunctionTable" = Relationship(back_populates="versions")
    prompt: Optional["PromptTable"] = Relationship(back_populates="version")
    spans: list["SpanTable"] = Relationship(
        back_populates="version", cascade_delete=True
    )
