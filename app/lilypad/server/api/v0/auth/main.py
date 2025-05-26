"""The `/api/v0/auth` FastAPI sub-app for `lilypad`."""

from fastapi import APIRouter

from .github_api import github_router
from .google_api import google_router

auth_router = APIRouter(prefix="/auth")
auth_router.include_router(github_router)
auth_router.include_router(google_router)


__all__ = ["auth_router"]
