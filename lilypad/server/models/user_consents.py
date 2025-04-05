"""Model for storing user consent."""

from datetime import datetime
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from pydantic import AwareDatetime
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel

from .base_sql_model import BaseSQLModel
from .table_names import USER_CONSENT_TABLE_NAME, USER_TABLE_NAME

if TYPE_CHECKING:
    from .users import UserTable


class UserConsentBase(SQLModel):
    """Base User Consent Model."""

    privacy_policy_version: str = Field(
        default="2025-04-04",
        description="Last updated date of the privacy policy accepted",
    )
    privacy_policy_accepted_at: Annotated[datetime, AwareDatetime] = Field(
        sa_type=DateTime(timezone=True),  # pyright: ignore [reportArgumentType]
        nullable=False,
        schema_extra={"format": "date-time"},
    )
    tos_version: str = Field(
        default="2025-04-04",
        description="Last updated date of the terms of service accepted",
    )
    tos_accepted_at: Annotated[datetime, AwareDatetime] = Field(
        sa_type=DateTime(timezone=True),  # pyright: ignore [reportArgumentType]
        nullable=False,
        schema_extra={"format": "date-time"},
    )


class UserConsentTable(UserConsentBase, BaseSQLModel, table=True):
    """User Consent table."""

    __tablename__ = USER_CONSENT_TABLE_NAME  # type: ignore
    user_uuid: UUID = Field(
        foreign_key=f"{USER_TABLE_NAME}.uuid",
        nullable=False,
        description="ID of the user",
    )

    user: "UserTable" = Relationship(back_populates="user_consents")
