"""The `/user-consents` API router."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from ..._utils import get_current_user
from ...models.user_consents import UserConsentTable
from ...schemas.user_consents import (
    UserConsentCreate,
    UserConsentPublic,
    UserConsentUpdate,
)
from ...schemas.users import UserPublic
from ...services.user_consents import UserConsentService

user_consents_router = APIRouter()


@user_consents_router.post("/user-consents", response_model=UserConsentPublic)
def post_user_consent(
    user: Annotated[UserPublic, Depends(get_current_user)],
    user_consent_service: Annotated[UserConsentService, Depends(UserConsentService)],
    data: UserConsentCreate,
) -> UserConsentTable:
    """Store user consent."""
    now = datetime.now(timezone.utc)
    data.privacy_policy_accepted_at = now
    data.tos_accepted_at = now
    data.user_uuid = user.uuid
    return user_consent_service.create_record(data)


@user_consents_router.patch(
    "/user-consents/{user_consent_uuid}", response_model=UserConsentPublic
)
def update_user_consent(
    user_consent_uuid: UUID,
    user_consent_service: Annotated[UserConsentService, Depends(UserConsentService)],
    user_consent_update: UserConsentUpdate,
) -> UserConsentTable:
    """Update user consent."""
    now = datetime.now(timezone.utc)
    if user_consent_update.privacy_policy_version is not None:
        user_consent_update.privacy_policy_accepted_at = now
    if user_consent_update.tos_version is not None:
        user_consent_update.tos_accepted_at = now
    return user_consent_service.update_record_by_uuid(
        user_consent_uuid,
        user_consent_update.model_dump(exclude_unset=True),
    )
