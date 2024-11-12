"""The `/api/v0` FastAPI sub-app for `lilypad`."""

from fastapi import FastAPI

from .projects_api import projects_router
from .prompts_api import prompts_router
from .spans_api import spans_router
from .traces_api import traces_router
from .versions_api import versions_router

api = FastAPI()
api.include_router(projects_router)
api.include_router(prompts_router)
api.include_router(spans_router)
api.include_router(traces_router)
api.include_router(versions_router)


__all__ = ["api"]
