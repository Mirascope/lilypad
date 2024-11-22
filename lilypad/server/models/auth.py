"""Auth models."""

from collections.abc import Sequence
from enum import Enum

from pydantic import BaseModel
from workos.organizations import Organization


class LoginType(str, Enum):
    """Login type enum"""

    GITHUB_OAUTH = "GitHubOAuth"
    GOOGLE_OAUTH = "GoogleOAuth"


class UserBase(BaseModel):
    """Base user model"""

    first_name: str | None = None
    raw_profile: dict
    session_id: str
    expires_at: str
    access_token: str | None = None
    organization_id: str | None = None
    organizations: Sequence[Organization] | None = None


class UserSession(UserBase):
    """User session model"""

    id: str | None = None


class User(UserBase):
    """User model"""

    id: str
