"""Call model"""

import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from lilypad.server.models import BaseSQLModel

from .table_names import CALL_TABLE_NAME, PROMPT_VERSION_TABLE_NAME

if TYPE_CHECKING:
    from lilypad.server.models import PromptVersionTable


class CallBase(BaseSQLModel):
    """Call model"""

    prompt_version_id: int = Field(
        default=None, foreign_key=f"{PROMPT_VERSION_TABLE_NAME}.id"
    )
    input: str
    output: str
    created_at: datetime.datetime = Field(
        default=datetime.datetime.now(datetime.UTC), nullable=False
    )


class CallTable(CallBase, table=True):
    """Call table"""

    __tablename__ = CALL_TABLE_NAME  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    prompt_version: "PromptVersionTable" = Relationship(back_populates="calls")
