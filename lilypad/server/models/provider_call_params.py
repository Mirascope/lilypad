from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from lilypad.server.models.base_sql_model import BaseSQLModel

from .table_names import (
    LLM_FUNCTION_TABLE_NAME,
    PROVIDER_CALL_PARAMS_TABLE_NAME,
)

if TYPE_CHECKING:
    from lilypad.server.models import LLMFunctionTable


class Provider(str, Enum):
    """Provider name enum"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ProviderCallParamsBase(BaseSQLModel):
    """Provider call params base model"""

    # project_id: int = Field(default=None, foreign_key=f"{PROJECT_TABLE_NAME}.id")
    llm_function_id: int | None = Field(foreign_key=f"{LLM_FUNCTION_TABLE_NAME}.id")
    provider: Provider
    model: str
    prompt_template: str
    editor_state: str
    call_params: str | None = Field(default=None)


class ProviderCallParamsTable(ProviderCallParamsBase, table=True):
    """Provider call params table"""

    __tablename__ = PROVIDER_CALL_PARAMS_TABLE_NAME  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    llm_function: "LLMFunctionTable" = Relationship(
        back_populates="provider_call_params"
    )
