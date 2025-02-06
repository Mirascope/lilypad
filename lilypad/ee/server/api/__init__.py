"""The `/ee/server/api` app for the main FastAPI server."""

from .v0 import ee_api as v0_ee_api

__all__ = ["v0_ee_api"]
