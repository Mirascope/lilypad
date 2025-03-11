"""The `/organizations` API router."""

import secrets
from typing import Annotated
from uuid import UUID

import resend
import resend.exceptions
from fastapi import APIRouter, Depends, HTTPException, status

from ee import LicenseError, LicenseValidator

from ..._utils import get_current_user
from ...models import (
    OrganizationInviteTable,
    OrganizationTable,
)
from ...schemas import (
    OrganizationInviteCreate,
    OrganizationInvitePublic,
    OrganizationPublic,
    UserPublic,
    UserRole,
)
from ...schemas.organizations import OrganizationUpdate
from ...services import OrganizationInviteService, OrganizationService
from ...settings import get_settings

organization_router = APIRouter()


@organization_router.get(
    "/organizations/invites/{invite_token}",
    response_model=OrganizationInvitePublic,
)
async def get_organization_invite(
    invite_token: str,
    organization_invite_service: Annotated[
        OrganizationInviteService, Depends(OrganizationInviteService)
    ],
) -> OrganizationInviteTable:
    """Get an organization invite."""
    return organization_invite_service.find_record_by_token(invite_token)


@organization_router.post(
    "/organizations/invites",
    response_model=OrganizationInvitePublic,
)
async def create_organization_invite(
    user: Annotated[UserPublic, Depends(get_current_user)],
    organization_invite_service: Annotated[
        OrganizationInviteService, Depends(OrganizationInviteService)
    ],
    organization_service: Annotated[OrganizationService, Depends(OrganizationService)],
    data: OrganizationInviteCreate,
) -> OrganizationInvitePublic:
    """Create an organization invite."""
    invite_token = secrets.token_urlsafe(32)
    data.token = invite_token
    data.organization_uuid = user.active_organization_uuid
    if not user.active_organization_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have an active organization.",
        )
    organization = organization_service.find_record_by_uuid(
        user.active_organization_uuid
    )
    settings = get_settings()
    resend.api_key = settings.resend_api_key
    invite_link = f"{settings.client_url}/join/{invite_token}"
    if settings.resend_api_key:
        params: resend.Emails.SendParams = {
            "from": "Lilypad Team <team@lilypad.so>",
            "to": [data.email],
            "subject": f"You have been invited to join {organization.name} on Lilypad",
            "html": f"""
                    <h1>Join {organization.name} on Lilypad</h1>
                    <p>You have been invited by {user.first_name} to join {organization.name}.</p>
                    <p>To accept the invite, click the link below.</p>
                    <a href="{invite_link}">Accept Invitation</a>
                """,
            "text": f"You have been invited by {user.first_name} to join {organization.name}. To accept the invite, copy the link: {invite_link}",
        }
        try:
            email = resend.Emails.send(params)
        except resend.exceptions.ResendError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email.",
            )
        data.resend_email_id = email["id"]
    else:
        data.resend_email_id = "n/a"
    organization_invite = organization_invite_service.create_record(data)
    return OrganizationInvitePublic.model_validate(
        organization_invite,
        update={
            "invite_link": invite_link,
        },
    )


@organization_router.patch(
    "/organizations/{organization_uuid}",
    response_model=OrganizationPublic,
)
async def update_organization(
    organization_uuid: UUID,
    organization_service: Annotated[OrganizationService, Depends(OrganizationService)],
    organization_update: OrganizationUpdate,
    user: Annotated[UserPublic, Depends(get_current_user)],
) -> OrganizationTable:
    """Update an organization."""
    # Check if user is in organization
    user_org = None
    for org in user.user_organizations or []:
        if org.organization_uuid == organization_uuid:
            user_org = org
            break
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
            validator.verify_license(new_license, organization_uuid)
        except LicenseError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid license key: {str(e)}",
            )

    return organization_service.update_record_by_uuid(organization_uuid, organization)
