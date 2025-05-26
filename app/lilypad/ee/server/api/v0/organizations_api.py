"""The EE `/annotations` API router."""

from typing import Annotated

from fastapi import APIRouter, Depends

from ee.validate import LicenseInfo

from ...require_license import get_organization_license

organizations_router = APIRouter()


@organizations_router.get("/organizations/license", response_model=LicenseInfo)
async def get_license(
    license: Annotated[LicenseInfo, Depends(get_organization_license)],
) -> LicenseInfo:
    """Get the license information for the organization"""
    return license
