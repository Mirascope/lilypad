"""The `v0` API for the `/ee/server/api` FastAPI sub-app."""

from fastapi import APIRouter

from .annotations_api import annotations_router
from .environment_api import environment_router
from .generations_api import generations_router
from .organization_invites_api import organization_invites_router
from .organizations_api import organizations_router
from .user_organizations_api import user_organizations_router

ee_router = APIRouter(prefix="/ee")
ee_router.include_router(annotations_router)
ee_router.include_router(environment_router)
ee_router.include_router(generations_router)
ee_router.include_router(organizations_router)
ee_router.include_router(organization_invites_router)
ee_router.include_router(user_organizations_router)

__all__ = ["ee_router"]
