"""The `v0` API for the `/ee/server//api` FastAPI sub-app."""

from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status

from ee.validate import LicenseInfo, LicenseValidator

from .....server.services import OrganizationService, ProjectService
from .annotations_api import Tier, annotations_router

ee_api = FastAPI(separate_input_output_schemas=False)
ee_api.include_router(annotations_router)


@ee_api.get("/projects/{project_uuid}", response_model=LicenseInfo)
async def get_license(
    project_uuid: UUID,
    project_service: Annotated[ProjectService, Depends(ProjectService)],
    organization_service: Annotated[OrganizationService, Depends(OrganizationService)],
) -> LicenseInfo:
    project = project_service.find_record_by_uuid(project_uuid)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    if not project.organization_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project does not belong to an organization",
        )
    organization_uuid = project.organization_uuid

    validator = LicenseValidator()
    license_info = validator.validate_license(organization_uuid, organization_service)
    if not license_info:
        return LicenseInfo(
            customer="",
            license_id="",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            tier=Tier.FREE,
            organization_uuid=organization_uuid,
        )
    return license_info


__all__ = ["ee_api"]
