"""FnParams Models."""

from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from lilypad.server.models import BaseSQLModel

from .table_names import (
    FN_PARAMS_TABLE_NAME,
    LLM_FN_TABLE_NAME,
)

if TYPE_CHECKING:
    from lilypad.server.models import LLMFunctionTable, VersionTable


class Provider(str, Enum):
    """Provider name enum"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class FnParamsBase(BaseSQLModel):
    """Provider call params base model"""

    llm_function_id: int | None = Field(foreign_key=f"{LLM_FN_TABLE_NAME}.id")
    provider: Provider
    hash: str | None = Field(default=None)
    model: str
    prompt_template: str
    editor_state: str
    call_params: str | None = Field(default=None)


class FnParamsTable(FnParamsBase, table=True):
    """Provider call params table"""

    __tablename__ = FN_PARAMS_TABLE_NAME  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    llm_fn: "LLMFunctionTable" = Relationship(back_populates="fn_params")
    version: "VersionTable" = Relationship(back_populates="fn_params")
