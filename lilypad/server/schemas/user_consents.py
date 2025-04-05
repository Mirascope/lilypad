"""UserConsent schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from ..models.user_consents import UserConsentBase


class UserConsentPublic(UserConsentBase):
    """UserConsent public model."""

    uuid: UUID


class UserConsentCreate(BaseModel):
    """UserConsent create model."""

    privacy_policy_version: str
    privacy_policy_accepted_at: datetime | None = None
    tos_version: str
    tos_accepted_at: datetime | None = None
    user_uuid: UUID | None = None


class UserConsentUpdate(BaseModel):
    """UserConsent update model."""

    privacy_policy_version: str | None = None
    privacy_policy_accepted_at: datetime | None = None
    tos_version: str | None = None
    tos_accepted_at: datetime | None = None
