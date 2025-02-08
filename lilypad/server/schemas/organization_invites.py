"""Organization invites schemas."""

from uuid import UUID

from ..models.organization_invites import OrganizationInviteBase
from .users import UserPublic


class OrganizationInvitePublic(OrganizationInviteBase):
    """OrganizationInvite public model"""

    uuid: UUID
    organization_uuid: UUID
    user: UserPublic
    resend_email_id: str
    invite_link: str | None = None


class OrganizationInviteCreate(OrganizationInviteBase):
    """OrganizationInvite create model"""

    token: str | None = None
    resend_email_id: str | None = None
    organization_uuid: UUID | None = None
