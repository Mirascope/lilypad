"""Users schemas."""

from uuid import UUID

from pydantic import BaseModel, Field

from .user_organizations import UserOrganizationPublic


class UserPublic(BaseModel):
    """User public model"""

    uuid: UUID
    first_name: str
    last_name: str | None = None
    email: str
    active_organization_uuid: UUID | None = None
    keys: dict[str, str] = Field(default_factory=dict)
    access_token: str | None = None
    user_organizations: list[UserOrganizationPublic] | None = None


class UserCreate(BaseModel):
    """User create model"""

    first_name: str
    last_name: str | None = None
    email: str
    active_organization_uuid: UUID | None = None
