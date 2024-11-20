"""Auth models."""

from pydantic import BaseModel


class UserBase(BaseModel):
    """Base user model"""

    first_name: str | None = None
    raw_profile: dict
    session_id: str
    expires_at: str
    access_token: str | None = None


class UserSession(UserBase):
    """User session model"""

    id: str | None = None


class User(UserBase):
    """User model"""

    id: str
