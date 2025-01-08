"""The `/api/v0` FastAPI sub-app for `lilypad`."""

from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel

from ...settings import Settings, get_settings
from .auth import auth_router
from .device_codes_api import device_codes_api
from .generations_api import generations_router
from .projects_api import projects_router
from .prompts_api import prompts_router
from .response_models_api import response_models_router
from .spans_api import spans_router
from .traces_api import traces_router
from .users_api import users_router

api = FastAPI()
api.include_router(device_codes_api)
api.include_router(generations_router)
api.include_router(projects_router)
api.include_router(prompts_router)
api.include_router(response_models_router)
api.include_router(spans_router)
api.include_router(traces_router)
api.include_router(auth_router)
api.include_router(users_router)


class SettingsPublic(BaseModel):
    remote_base_url: str
    github_client_id: str
    environment: str


@api.get("/settings", response_model=SettingsPublic)
async def get_settings_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> SettingsPublic:
    """Get the configuration."""
    return SettingsPublic(
        remote_base_url=settings.remote_base_url,
        github_client_id=settings.github_client_id,
        environment=settings.environment,
    )


__all__ = ["api"]
