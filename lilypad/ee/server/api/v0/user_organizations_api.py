"""The EE `/user-organizations` API router."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from ee.validate import LicenseValidator, Tier

from .....server._utils import get_current_user
from .....server._utils.auth import create_jwt_token
from .....server.models import UserTable
from .....server.schemas.users import (
    UserPublic,
)
from .....server.services import (
    OrganizationInviteService,
    OrganizationService,
    UserService,
)
from .....server.services.billing import BillingService
from ....server.features import cloud_features
from ....server.require_license import is_lilypad_cloud
from ...models import UserOrganizationTable, UserRole
from ...schemas.user_organizations import UserOrganizationCreate, UserOrganizationUpdate
from ...services import UserOrganizationService

user_organizations_router = APIRouter()


@user_organizations_router.get(
    "/user-organizations/users", response_model=Sequence[UserPublic]
)
async def get_users_by_organization(
    user_organization_service: Annotated[
        UserOrganizationService, Depends(UserOrganizationService)
    ],
) -> Sequence[UserTable]:
    """Get all users of an organization."""
    return [
        user_org.user
        for user_org in user_organization_service.get_users_by_active_organization()
    ]


@user_organizations_router.get(
    "/user-organizations", response_model=Sequence[UserOrganizationTable]
)
async def get_user_organizations(
    user_organization_service: Annotated[
        UserOrganizationService, Depends(UserOrganizationService)
    ],
) -> Sequence[UserOrganizationTable]:
    """Get all user organizations."""
    return user_organization_service.get_users_by_active_organization()


class CreateUserOrganizationToken(BaseModel):
    """Create user organization token model"""

    token: str


@user_organizations_router.post("/user-organizations", response_model=UserPublic)
async def create_user_organization(
    user_organization_service: Annotated[
        UserOrganizationService, Depends(UserOrganizationService)
    ],
    organization_invites_service: Annotated[
        OrganizationInviteService, Depends(OrganizationInviteService)
    ],
    organization_service: Annotated[OrganizationService, Depends(OrganizationService)],
    create_user_organization_token: CreateUserOrganizationToken,
    user: Annotated[UserPublic, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(UserService)],
    request: Request = None, # pyright: ignore[reportArgumentType]
    billing_service: Annotated[BillingService | None, Depends(BillingService)] = None,
) -> UserPublic:
    """Create user organization"""
    org_invite = organization_invites_service.find_record_by_token(
        create_user_organization_token.token
    )
    if not org_invite or not org_invite.uuid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found.",
        )
    # OPEN BETA: Limit number of users per organization based on tier

    is_cloud = request is not None and is_lilypad_cloud(request)

    # For Lilypad Cloud, get tier from billing table
    tier = Tier.FREE
    if is_cloud and billing_service is not None:
        tier = billing_service.get_tier_from_billing(org_invite.organization_uuid)
    else:
        # For self-hosted, use license validator
        validator = LicenseValidator()
        license_info = validator.validate_license(
            org_invite.organization_uuid, organization_service
        )
        if license_info:
            tier = license_info.tier
    num_users = user_organization_service.count_users_in_organization(
        org_invite.organization_uuid
    )
    if num_users >= cloud_features[tier].num_users_per_organization:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Exceeded the maximum number of users ({cloud_features[tier].num_users_per_organization}) for {tier.name.capitalize()} plan",
        )
    invite_deleted = organization_invites_service.delete_record_by_uuid(
        org_invite.uuid,
    )
    if not invite_deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete invite.",
        )
    data = UserOrganizationCreate(
        role=UserRole.MEMBER,
        user_uuid=user.uuid,
    )
    user_organization = user_organization_service.create_record(
        data, organization_uuid=org_invite.organization_uuid
    )
    if not user_organization:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user organization.",
        )
    # Update user active organization
    new_user = user_service.update_user_active_organization_uuid(
        user_organization.organization_uuid
    )
    user_public = UserPublic.model_validate(new_user)
    user_public.access_token = create_jwt_token(user_public)
    return user_public


@user_organizations_router.patch(
    "/user-organizations/{user_organization_uuid}", response_model=UserOrganizationTable
)
async def update_user_organization(
    user_organization_uuid: UUID,
    data: UserOrganizationUpdate,
    user_organization_service: Annotated[
        UserOrganizationService, Depends(UserOrganizationService)
    ],
) -> UserOrganizationTable:
    """Updates user organization"""
    return user_organization_service.update_record_by_uuid(
        user_organization_uuid, data.model_dump(exclude_unset=True)
    )


@user_organizations_router.delete("/user-organizations/{user_organization_uuid}")
async def delete_user_organizations(
    user_organization_uuid: UUID,
    user_organization_service: Annotated[
        UserOrganizationService, Depends(UserOrganizationService)
    ],
) -> bool:
    """Delete user organization by uuid"""
    return user_organization_service.delete_record_by_uuid(user_organization_uuid)
