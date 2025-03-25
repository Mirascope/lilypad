"""The `/organizations` API router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ee import LicenseValidator
from ee.validate import LicenseError

from ....ee.server.models.user_organizations import UserRole
from ..._utils import get_current_user
from ...models import (
    OrganizationTable,
)
from ...schemas import (
    OrganizationPublic,
    UserPublic,
)
from ...schemas.organizations import OrganizationUpdate
from ...services import OrganizationService

organization_router = APIRouter()


@organization_router.patch(
    "/organizations",
    response_model=OrganizationPublic,
)
async def update_organization(
    organization_service: Annotated[OrganizationService, Depends(OrganizationService)],
    organization_update: OrganizationUpdate,
    user: Annotated[UserPublic, Depends(get_current_user)],
) -> OrganizationTable:
    """Update an organization."""
    # Check if user is in organization
    user_org = None
    for org in user.user_organizations or []:
        if org.organization_uuid == user.active_organization_uuid:
            user_org = org
            break
    if not user.active_organization_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have an active organization",
        )
    if not user_org:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this organization",
        )
    if not user_org.role == UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owner can update organization",
        )

    # If updating license, validate it
    organization = organization_update.model_dump(exclude_unset=True)
    if (
        "license" in organization
        and (new_license := organization["license"]) is not None
    ):
        try:
            validator = LicenseValidator()
            validator.verify_license(new_license, user.active_organization_uuid)
        except LicenseError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid license key: {str(e)}",
            )

    return organization_service.update_record_by_uuid(
        user.active_organization_uuid, organization
    )
