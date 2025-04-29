"""Secrets schema."""

from pydantic import BaseModel, Field, field_validator

from .._utils.security import mask_secret


class ExternalAPIKeyCreate(BaseModel):
    """Request model for creating a secret."""

    service_name: str
    api_key: str = Field(..., description="New API key", min_length=1)


class ExternalAPIKeyUpdate(BaseModel):
    """Request model for updating a secret."""

    api_key: str = Field(..., description="New API key", min_length=1)


class ExternalAPIKeyPublic(BaseModel):
    """Response model for a secret."""

    service_name: str
    masked_api_key: str = Field(..., description="Partially masked API key")

    @field_validator("masked_api_key")
    def make_masked_key(cls, value: str) -> str:
        """Mask the API key."""
        return mask_secret(value, visible_chars=4)
