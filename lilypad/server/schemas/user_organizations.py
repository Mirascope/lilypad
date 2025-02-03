"""Users organizations schemas."""

from uuid import UUID

from pydantic import BaseModel

from ..models.user_organizations import UserRole, _UserOrganizationBase
from . import OrganizationPublic


class UserOrganizationPublic(_UserOrganizationBase):
    """UserOrganization public model"""

    uuid: UUID
    organization_uuid: UUID
    organization: OrganizationPublic


class UserOrganizationCreate(BaseModel):
    """UserOrganization create model"""

    role: UserRole
