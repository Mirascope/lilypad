"""The `/users` API router."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from ...models import UserPublic, UserTable
from ...services import UserService

users_router = APIRouter()


@users_router.put("/users/{activeOrganizationUuid}", response_model=UserPublic)
async def update_user_active_organization_id(
    activeOrganizationUuid: UUID,
    user_service: Annotated[UserService, Depends(UserService)],
) -> UserTable:
    """Update users active organization uuid."""
    return user_service.update_user_active_organization_uuid(activeOrganizationUuid)


__all__ = ["users_router"]
