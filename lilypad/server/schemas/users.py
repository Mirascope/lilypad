"""Users schemas."""

from uuid import UUID

from pydantic import BaseModel, Field

from ..models.users import UserBase
from .user_organizations import UserOrganizationPublic


class UserPublic(UserBase):
    """User public model"""

    uuid: UUID
    access_token: str | None = None
    user_organizations: list[UserOrganizationPublic] | None = None
    scopes: list[str] = Field(default_factory=list)


class UserCreate(BaseModel):
    """User create model"""

    first_name: str
    last_name: str | None = None
    email: str
    active_organization_uuid: UUID | None = None
