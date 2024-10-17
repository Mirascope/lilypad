"""Project model"""

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship

from lilypad.server.models import BaseSQLModel

from .table_names import LLM_FN_TABLE_NAME, PROJECT_TABLE_NAME

if TYPE_CHECKING:
    from lilypad.server.models import (
        FnParamsTable,
        ProjectTable,
        VersionTable,
    )


class LLMFunctionBase(BaseSQLModel):
    """LLM function base model"""

    function_name: str = Field(nullable=False, index=True)
    version_hash: str = Field(nullable=False, index=True)
    code: str
    arg_types: dict[str, str] | None = Field(
        sa_column=Column(JSON), default_factory=dict
    )


class LLMFunctionTable(LLMFunctionBase, table=True):
    """LLM function table"""

    __tablename__ = LLM_FN_TABLE_NAME  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(default=None, foreign_key=f"{PROJECT_TABLE_NAME}.id")
    created_at: datetime.datetime = Field(
        default=datetime.datetime.now(datetime.timezone.utc), nullable=False
    )

    fn_params: list["FnParamsTable"] = Relationship(back_populates="llm_fn")
    project: "ProjectTable" = Relationship(back_populates="llm_fns")
    version: "VersionTable" = Relationship(back_populates="llm_fn")
