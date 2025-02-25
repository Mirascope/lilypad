"""The `v0` API for the `/ee/server//api` FastAPI sub-app."""

from fastapi import FastAPI

from .annotations_api import annotations_router

ee_api = FastAPI(separate_input_output_schemas=False)
ee_api.include_router(annotations_router)


__all__ = ["ee_api"]
