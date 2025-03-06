"""The `v0` API for the `/ee/server//api` FastAPI sub-app."""

from typing import Annotated

from fastapi import Depends, FastAPI

from ee.validate import LicenseInfo
from lilypad.ee.server.require_license import _RequireLicense

from .annotations_api import Tier, annotations_router

ee_api = FastAPI(separate_input_output_schemas=False)
ee_api.include_router(annotations_router)


@ee_api.get("/projects/{project_uuid}", response_model=Tier)
async def root(
    license_info: Annotated[
        LicenseInfo | None, Depends(_RequireLicense(tier=Tier.ENTERPRISE))
    ],
) -> Tier:
    if not license_info:
        return Tier.FREE
    return license_info.tier


__all__ = ["ee_api"]
