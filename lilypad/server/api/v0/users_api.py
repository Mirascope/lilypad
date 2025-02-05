"""The `/users` API router."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..._utils import create_jwt_token, get_current_user
from ...models import (
    UserOrganizationTable,
    UserRole,
    UserTable,
)
from ...schemas import UserOrganizationCreate, UserOrganizationUpdate, UserPublic
from ...services import OrganizationInviteService, UserOrganizationService, UserService

users_router = APIRouter()


@users_router.get("/user-organizations/users", response_model=Sequence[UserPublic])
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


@users_router.get("/user-organizations", response_model=Sequence[UserOrganizationTable])
async def get_user_organizations(
    user_organization_service: Annotated[
        UserOrganizationService, Depends(UserOrganizationService)
    ],
) -> Sequence[UserOrganizationTable]:
    """Get all user organizations."""
    return user_organization_service.get_users_by_active_organization()


class CreateUserOrganizationToken(BaseModel):
    token: str


@users_router.post("/user-organizations", response_model=UserOrganizationTable)
async def create_user_organization(
    user_organization_service: Annotated[
        UserOrganizationService, Depends(UserOrganizationService)
    ],
    organization_invites_service: Annotated[
        OrganizationInviteService, Depends(OrganizationInviteService)
    ],
    create_user_organization_token: CreateUserOrganizationToken,
    user: Annotated[UserPublic, Depends(get_current_user)],
) -> UserOrganizationTable:
    """Create user organization"""
    org_invite = organization_invites_service.find_record_by_token(
        create_user_organization_token.token
    )
    if not org_invite or not org_invite.uuid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found.",
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
    return user_organization


@users_router.patch(
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


@users_router.delete("/user-organizations/{user_organization_uuid}")
async def delete_user_organizations(
    user_organization_uuid: UUID,
    user_organization_service: Annotated[
        UserOrganizationService, Depends(UserOrganizationService)
    ],
) -> bool:
    """Delete user organization by uuid"""
    return user_organization_service.delete_record_by_uuid(user_organization_uuid)


@users_router.put("/users/{activeOrganizationUuid}", response_model=UserPublic)
async def update_user_active_organization_id(
    activeOrganizationUuid: UUID,
    user_service: Annotated[UserService, Depends(UserService)],
) -> UserPublic:
    """Update users active organization uuid."""
    user = user_service.update_user_active_organization_uuid(activeOrganizationUuid)
    user_public = UserPublic.model_validate(user)
    user_public.access_token = create_jwt_token(user_public)
    return user_public


@users_router.patch("/users", response_model=UserPublic)
async def update_user_keys(
    user_service: Annotated[UserService, Depends(UserService)],
    data: dict,
) -> UserTable:
    """Update users keys."""
    return user_service.update_user_keys(data)


@users_router.get("/current-user", response_model=UserPublic)
async def get_user(
    user_service: Annotated[UserService, Depends(UserService)],
) -> UserPublic:
    """Get user."""
    return user_service.user


__all__ = ["users_router"]
