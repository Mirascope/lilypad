"""The `/ee/server/api/v0` FastAPI sub-app for `lilypad`."""

from pydantic import BaseModel

from .....server.api.v0 import api
from .datasets_api import datasets_router

api.include_router(datasets_router)


class SettingsPublic(BaseModel):
    remote_client_url: str
    remote_api_url: str
    github_client_id: str
    environment: str


__all__ = ["api"]
