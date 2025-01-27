"""The `/users` API router."""

from typing import Annotated, Sequence
from uuid import UUID

from fastapi import APIRouter, Depends

from ...models import UserPublic, UserTable
from ...services import UserOrganizationService, UserService

users_router = APIRouter()


@users_router.get("/users/organizations", response_model=Sequence[UserPublic])
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


@users_router.put("/users/{activeOrganizationUuid}", response_model=UserPublic)
async def update_user_active_organization_id(
    activeOrganizationUuid: UUID,
    user_service: Annotated[UserService, Depends(UserService)],
) -> UserTable:
    """Update users active organization uuid."""
    return user_service.update_user_active_organization_uuid(activeOrganizationUuid)


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
