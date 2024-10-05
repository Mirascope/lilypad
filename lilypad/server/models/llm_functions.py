"""Project model"""

import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from lilypad.server.models import BaseSQLModel
from lilypad.server.models.provider_call_params import ProviderCallParamsTable

from .table_names import LLM_FUNCTION_TABLE_NAME

if TYPE_CHECKING:
    from lilypad.server.models import SpanTable


class LLMFunctionBase(BaseSQLModel):
    """LLM function base model"""

    # project_id: int = Field(default=None, foreign_key=f"{PROJECT_TABLE_NAME}.id")
    function_name: str = Field(nullable=False, index=True)
    version_hash: str | None = Field(default=None, index=True)
    code: str
    input_arguments: str | None = Field(default=None)


class LLMFunctionTable(LLMFunctionBase, table=True):
    """LLM function table"""

    __tablename__ = LLM_FUNCTION_TABLE_NAME  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime.datetime = Field(
        default=datetime.datetime.now(datetime.UTC), nullable=False
    )

    provider_call_params: list["ProviderCallParamsTable"] = Relationship(
        back_populates="llm_function"
    )

    spans: list["SpanTable"] = Relationship(back_populates="llm_function")
