"""Secrets schema."""

from pydantic import BaseModel, Field, field_validator

from .._utils.security import mask_secret


class SecretCreate(BaseModel):
    """Request model for storing or updating a secret."""

    service_name: str
    api_key: str


class SecretUpdate(BaseModel):
    """Request model for updating a secret."""

    api_key: str


class SecretPublic(BaseModel):
    """Display model for secrets with masked API key."""

    service_name: str
    api_key: str = Field(..., description="Partially masked API key")

    @field_validator("api_key")
    def make_masked_key(cls, value: str) -> str:
        """Mask the API key."""
        return mask_secret(value, visible_chars=4)
