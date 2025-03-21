"""The EE `/organization-invites` API router."""

import secrets
from typing import Annotated

import resend
import resend.exceptions
from fastapi import APIRouter, Depends, HTTPException, status

from .....server._utils import get_current_user
from .....server.schemas import (
    UserPublic,
)
from .....server.services import OrganizationService
from .....server.settings import get_settings
from ...models import (
    OrganizationInviteTable,
)
from ...schemas.organization_invites import (
    OrganizationInviteCreate,
    OrganizationInvitePublic,
)
from ...services import OrganizationInviteService

organization_invites_router = APIRouter()


@organization_invites_router.get(
    "/organizations-invites/{invite_token}",
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


@organization_invites_router.post(
    "/organizations-invites",
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
