"""The `v0` API for the `/ee/server/api` FastAPI sub-app."""

from fastapi import APIRouter

from .annotations_api import annotations_router
from .generations_api import generations_router
from .organizations_api import organizations_router
from .user_organizations_api import user_organizations_router

ee_router = APIRouter(prefix="/ee")
ee_router.include_router(annotations_router)
ee_router.include_router(generations_router)
ee_router.include_router(organizations_router)
ee_router.include_router(user_organizations_router)

__all__ = ["ee_router"]
