"""The `/ee/server/api` app for the main FastAPI server."""

from .v0 import ee_router as v0_ee_router

__all__ = ["v0_ee_router"]
