"""API endpoints for generations."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from ee import Tier
from lilypad.ee.server.services import (
    DeploymentService,
    GenerationService,
)
from lilypad.server.models import GenerationTable
from lilypad.server.schemas import GenerationPublic

from ..._utils import get_current_environment
from ...models.environments import Environment
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
    "/projects/{project_uuid}/generations/name/{generation_name}/environments",
    response_model=GenerationPublic,
)
@require_license(tier=Tier.ENTERPRISE)
async def get_deployed_generation_by_names(
    project_uuid: UUID,
    generation_name: str,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
    deployment_service: Annotated[DeploymentService, Depends(DeploymentService)],
    environment: Annotated[Environment, Depends(get_current_environment)],
) -> GenerationTable:
    """Get the deployed generation by generation name and environment name."""
    deployment = deployment_service.get_specific_deployment(
        project_uuid,
        environment.uuid,
        generation_name,  # pyright: ignore [reportArgumentType]
    )

    if not deployment:
        # get the latest generation as fallback
        latest_generation = generation_service.find_latest_generation_by_name(
            project_uuid, generation_name
        )
        if latest_generation:
            return latest_generation
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation '{generation_name}' is not deployed in environment '{environment.name}'",
        )

    if not deployment.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Generation '{generation_name}' is deployed but not active in environment '{environment.name}'",
        )

    return deployment.generation
