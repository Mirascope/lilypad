"""EE Users organizations schemas."""

from uuid import UUID

from pydantic import BaseModel

from ....server.schemas.organizations import OrganizationPublic
from ..models.user_organizations import UserOrganizationBase, UserRole


class UserOrganizationPublic(UserOrganizationBase):
    """UserOrganization public model"""

    uuid: UUID
    organization_uuid: UUID
    organization: OrganizationPublic


class UserOrganizationCreate(UserOrganizationBase):
    """UserOrganization create model"""

    role: UserRole


class UserOrganizationUpdate(BaseModel):
    """UserOrganization update model"""

    role: UserRole
