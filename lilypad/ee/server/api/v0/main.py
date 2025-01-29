"""The `/ee/server/api/v0` FastAPI sub-app for `lilypad`."""


from .....server.api.v0 import api
from .datasets_api import datasets_router

api.include_router(datasets_router)

__all__ = ["api"]
