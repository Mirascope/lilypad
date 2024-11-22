"""The `/api/v0` FastAPI sub-app for `lilypad`."""

from fastapi import FastAPI

from .auth_api import auth_router
from .device_codes_api import device_codes_api
from .functions_api import functions_router
from .projects_api import projects_router
from .prompts_api import prompts_router
from .spans_api import spans_router
from .traces_api import traces_router
from .versions_api import versions_router

api = FastAPI()
api.include_router(auth_router)
api.include_router(device_codes_api)
api.include_router(functions_router)
api.include_router(projects_router)
api.include_router(prompts_router)
api.include_router(spans_router)
api.include_router(traces_router)
api.include_router(versions_router)


__all__ = ["api"]
