"""Functions environment link model."""

from uuid import UUID

from sqlmodel import Field, SQLModel

from .table_names import (
    ENVIRONMENT_TABLE_NAME,
    FUNCTION_ENVIRONMENT_LINK_TABLE_NAME,
    FUNCTION_TABLE_NAME,
)


class FunctionEnvironmentLink(SQLModel, table=True):
    """Link table for tracking which functions have been used in which environments."""

    __tablename__ = FUNCTION_ENVIRONMENT_LINK_TABLE_NAME  # type: ignore

    function_uuid: UUID = Field(
        foreign_key=f"{FUNCTION_TABLE_NAME}.uuid", primary_key=True, ondelete="CASCADE"
    )
    environment_uuid: UUID = Field(
        foreign_key=f"{ENVIRONMENT_TABLE_NAME}.uuid",
        primary_key=True,
        ondelete="CASCADE",
    )
