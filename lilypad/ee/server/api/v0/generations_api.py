"""API endpoints for generations."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from starlette import status

from ee import Tier
from lilypad.ee.server.services import (
    DeploymentService,
    EnvironmentService,
    GenerationService,
)
from lilypad.server.models import GenerationTable
from lilypad.server.schemas import GenerationPublic

from ...models.environments import EnvironmentTable
from ...require_license import require_license

generations_router = APIRouter()


@generations_router.get(
    "/projects/{project_uuid}/generations/name/{generation_name}/version/{version_num}",
    response_model=GenerationPublic,
)
@require_license(tier=Tier.ENTERPRISE)
async def get_generation_by_version(
    project_uuid: UUID,
    generation_name: str,
    version_num: int,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> GenerationTable:
    """Get generation by name."""
    return generation_service.find_generations_by_version(
        project_uuid, generation_name, version_num
    )


@generations_router.get(
    "/projects/{project_uuid}/generations/name/{generation_name}",
    response_model=Sequence[GenerationPublic],
)
@require_license(tier=Tier.ENTERPRISE)
async def get_generations_by_name(
    project_uuid: UUID,
    generation_name: str,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> Sequence[GenerationTable]:
    """Get generation by name."""
    return generation_service.find_generations_by_name(project_uuid, generation_name)


@generations_router.get(
    "/projects/{project_uuid}/generations/name/{generation_name}/environments/{environment_name}",
    response_model=GenerationPublic,
)
@require_license(tier=Tier.ENTERPRISE)
async def get_deployed_generation_by_names(
    project_uuid: UUID,
    generation_name: str,
    environment_name: str,
    environment_service: Annotated[EnvironmentService, Depends(EnvironmentService)],
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
    deployment_service: Annotated[DeploymentService, Depends(DeploymentService)],
) -> GenerationTable:
    """Get the deployed generation by generation name and environment name."""
    environment = environment_service.session.exec(
        select(EnvironmentTable).where(
            EnvironmentTable.organization_uuid
            == environment_service.user.active_organization_uuid,
            EnvironmentTable.project_uuid == project_uuid,
            EnvironmentTable.name == environment_name,
        )
    ).first()

    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment '{environment_name}' not found",
        )

    latest_generation = generation_service.find_latest_generation_by_name(
        project_uuid, generation_name
    )
    if not latest_generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation '{generation_name}' not found",
        )

    deployment = deployment_service.get_specific_deployment(
        environment.uuid, latest_generation.uuid  # pyright: ignore [reportArgumentType]
    )

    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation '{generation_name}' is not deployed in environment '{environment_name}'",
        )

    if not deployment.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Generation '{generation_name}' is deployed but not active in environment '{environment_name}'",
        )

    return latest_generation
