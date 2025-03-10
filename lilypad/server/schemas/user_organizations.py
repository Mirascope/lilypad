"""Users organizations schemas."""

from uuid import UUID

from pydantic import BaseModel

from ..models.user_organizations import UserRole
from .organizations import OrganizationPublic


class UserOrganizationPublic(BaseModel):
    """UserOrganization public model"""

    uuid: UUID
    role: UserRole
    user_uuid: UUID
    organization_uuid: UUID
    organization: OrganizationPublic


class UserOrganizationCreate(BaseModel):
    """UserOrganization create model"""

    role: UserRole
    user_uuid: UUID


class UserOrganizationUpdate(BaseModel):
    """UserOrganization update model"""

    role: UserRole
