"""Project model"""

import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from lilypad.server.models import BaseSQLModel

from .table_names import LLM_FN_TABLE_NAME, PROJECT_TABLE_NAME

if TYPE_CHECKING:
    from lilypad.server.models import (
        FnParamsTable,
        ProjectTable,
        SpanTable,
        VersionTable,
    )


class LLMFunctionBase(BaseSQLModel):
    """LLM function base model"""

    project_id: int = Field(default=None, foreign_key=f"{PROJECT_TABLE_NAME}.id")
    function_name: str = Field(nullable=False, index=True)
    version_hash: str = Field(nullable=False, index=True)
    code: str
    arg_types: str | None = Field(default=None)


class LLMFunctionTable(LLMFunctionBase, table=True):
    """LLM function table"""

    __tablename__ = LLM_FN_TABLE_NAME  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime.datetime = Field(
        default=datetime.datetime.now(datetime.timezone.utc), nullable=False
    )

    fn_params: list["FnParamsTable"] = Relationship(back_populates="llm_fn")
    project: "ProjectTable" = Relationship(back_populates="llm_fns")
    spans: list["SpanTable"] = Relationship(back_populates="llm_fn")
    version: "VersionTable" = Relationship(back_populates="llm_fn")
