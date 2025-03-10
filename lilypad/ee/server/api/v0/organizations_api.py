"""The EE `/annotations` API router."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ee.validate import LicenseInfo, LicenseValidator, Tier

from .....server._utils import get_current_user
from .....server.schemas import UserPublic
from .....server.services import OrganizationService

organizations_router = APIRouter()


@organizations_router.get("/organizations/license", response_model=LicenseInfo)
async def get_license(
    user: Annotated[UserPublic, Depends(get_current_user)],
    organization_service: Annotated[OrganizationService, Depends(OrganizationService)],
) -> LicenseInfo:
    """Get the license information for the organization"""
    if not user.active_organization_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have an active organization.",
        )
    validator = LicenseValidator()
    license_info = validator.validate_license(
        user.active_organization_uuid, organization_service
    )
    if not license_info:
        return LicenseInfo(
            customer="",
            license_id="",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            tier=Tier.FREE,
            organization_uuid=user.active_organization_uuid,
        )
    return license_info
