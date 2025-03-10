"""Organization invites schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from .users import UserPublic


class OrganizationInvitePublic(BaseModel):
    """OrganizationInvite public model"""

    uuid: UUID
    invited_by: UUID
    email: str
    expires_at: datetime
    organization_uuid: UUID
    user: UserPublic
    resend_email_id: str
    invite_link: str | None = None


class OrganizationInviteCreate(BaseModel):
    """OrganizationInvite create model"""

    invited_by: UUID
    email: str
    expires_at: datetime
    token: str | None = None
    resend_email_id: str | None = None
    organization_uuid: UUID | None = None
