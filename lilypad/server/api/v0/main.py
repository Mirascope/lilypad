"""The `/api/v0` FastAPI sub-app for `lilypad`."""

from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel

from ....ee.server.api import v0_ee_api
from ...settings import Settings, get_settings
from .api_keys_api import api_keys_api
from .auth import auth_router
from .generations_api import generations_router
from .organizations_api import organization_router
from .projects_api import projects_router
from .spans_api import spans_router
from .traces_api import traces_router
from .users_api import users_router

api = FastAPI(separate_input_output_schemas=False)
# The `/ee` FastAPI sub-app for `lilypad`.
api.mount("/ee", v0_ee_api)
api.include_router(api_keys_api)
api.include_router(generations_router)
api.include_router(projects_router)
api.include_router(spans_router)
api.include_router(traces_router)
api.include_router(auth_router)
api.include_router(users_router)
api.include_router(organization_router)


class SettingsPublic(BaseModel):
    remote_client_url: str
    remote_api_url: str
    github_client_id: str
    google_client_id: str
    environment: str
    experimental: bool


@api.get("/settings", response_model=SettingsPublic)
async def get_settings_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> SettingsPublic:
    """Get the configuration."""
    return SettingsPublic(
        remote_client_url=settings.remote_client_url,
        remote_api_url=settings.remote_api_url,
        github_client_id=settings.github_client_id,
        google_client_id=settings.google_client_id,
        environment=settings.environment,
        experimental=settings.experimental,
    )


__all__ = ["api"]
