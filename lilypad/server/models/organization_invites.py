"""Organization invites table and models."""

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base_organization_sql_model import BaseOrganizationSQLModel
from .table_names import ORGANIZATION_INVITE_TABLE_NAME, USER_TABLE_NAME

if TYPE_CHECKING:
    from .users import UserTable


class OrganizationInviteBase(SQLModel):
    """Base OrganizationInvite Model."""

    invited_by: UUID = Field(
        index=True, foreign_key=f"{USER_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    email: str = Field(nullable=False, min_length=1)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=7),
        nullable=False,
    )


class OrganizationInviteTable(
    OrganizationInviteBase, BaseOrganizationSQLModel, table=True
):
    """OrganizationInvite table."""

    __tablename__ = ORGANIZATION_INVITE_TABLE_NAME  # type: ignore

    token: str = Field(unique=True, nullable=False)
    resend_email_id: str
    user: "UserTable" = Relationship(back_populates="organization_invites")
