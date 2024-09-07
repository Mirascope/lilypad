"""Project model"""

import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from lilypad.app.models import BaseSQLModel

from .table_names import CALL_TABLE_NAME, PROMPT_VERSION_TABLE_NAME

if TYPE_CHECKING:
    from lilypad.app.models import PromptVersionTable


class CallTable(BaseSQLModel, table=True):
    """Call model"""

    __tablename__ = CALL_TABLE_NAME  # type: ignore

    id: int = Field(default=None, primary_key=True)
    prompt_version_id: int = Field(
        default=None, foreign_key=f"{PROMPT_VERSION_TABLE_NAME}.id"
    )
    input: str = Field(nullable=False)
    output: str = Field(nullable=False)
    created_at: datetime.datetime = Field(
        default=datetime.datetime.now(datetime.UTC), nullable=False
    )
    prompt_version: "PromptVersionTable" = Relationship(back_populates="calls")
