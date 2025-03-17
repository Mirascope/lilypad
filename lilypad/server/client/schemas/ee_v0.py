"""The Schema models for the Lilypad ee_v0 API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field


class Provider(str, Enum):
    """Provider name enum"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    GEMINI = "gemini"


class Tier(int, Enum):
    """License tier enum."""

    FREE = 0
    PRO = 1
    TEAM = 2
    ENTERPRISE = 3


class LicenseInfo(BaseModel):
    """Pydantic model for license validation"""

    customer: Annotated[str, Field(title="Customer")]
    license_id: Annotated[str, Field(title="License Id")]
    expires_at: Annotated[datetime, Field(title="Expires At")]
    tier: Tier
    organization_uuid: Annotated[UUID, Field(title="Organization Uuid")]
    is_expired: Annotated[bool, Field(title="Is Expired")]
    """
    Check if the license has expired
    """
