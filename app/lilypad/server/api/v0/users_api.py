"""The `/users` API router."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from ..._utils import create_jwt_token
from ...models.users import (
    UserTable,
)
from ...schemas.users import UserPublic
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


__all__ = ["users_router"]
