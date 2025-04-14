"""The `/users` API router."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from ..._utils import create_jwt_token, get_current_user
from ...models import (
    UserTable,
)
from ...schemas import UserPublic
from ...services import UserService

users_router = APIRouter()


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


@users_router.get("/users", response_model=UserPublic | None)
async def get_user_by_email(
    user_service: Annotated[UserService, Depends(UserService)],
    email: str,
    current_user: Annotated[UserPublic, Depends(get_current_user)] = None,
) -> UserTable | None:
    """Get user by email address within the current user's active organization."""
    if not current_user.active_organization_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user does not have an active organization selected.",
        )
    return user_service.find_record_by_email_in_organizations(
        email,
        [
            user_organizations.organization_uuid
            for user_organizations in current_user.user_organizations
        ],
    )


__all__ = ["users_router"]
