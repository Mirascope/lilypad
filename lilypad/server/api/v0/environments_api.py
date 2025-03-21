"""API endpoints for environments and deployments."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from lilypad.server.models import GenerationTable
from lilypad.server.schemas import GenerationPublic

from ....server.schemas import (
    DeploymentPublic,
    EnvironmentCreate,
    EnvironmentPublic,
)
from ....server.services import DeploymentService, EnvironmentService
from ...models.deployments import DeploymentTable
from ...models.environments import EnvironmentTable

environments_router = APIRouter()


# Environment endpoints
@environments_router.get("/environments", response_model=Sequence[EnvironmentPublic])
async def get_environments(
    environment_service: Annotated[EnvironmentService, Depends(EnvironmentService)],
) -> Sequence[EnvironmentTable]:
    """Get all environments for a project."""
    return environment_service.find_all_records()


@environments_router.post("/environments", response_model=EnvironmentPublic)
async def create_environment(
    environment_create: EnvironmentCreate,
    environment_service: Annotated[EnvironmentService, Depends(EnvironmentService)],
) -> EnvironmentTable:
    """Create a new environment."""
    return environment_service.create_record(environment_create)


@environments_router.get(
    "/environments/{environment_uuid}",
    response_model=EnvironmentPublic,
)
async def get_environment(
    environment_uuid: UUID,
    environment_service: Annotated[EnvironmentService, Depends(EnvironmentService)],
) -> EnvironmentTable:
    """Get environment by UUID."""
    return environment_service.find_record_by_uuid(environment_uuid)


@environments_router.delete("/environments/{environment_uuid}")
async def delete_environment(
    environment_uuid: UUID,
    environment_service: Annotated[EnvironmentService, Depends(EnvironmentService)],
) -> bool:
    """Delete an environment."""
    return environment_service.delete_record_by_uuid(environment_uuid)


# Deployment endpoints
@environments_router.post(
    "/projects/{project_uuid}/environments/{environment_uuid}/deploy",
    response_model=DeploymentPublic,
)
async def deploy_generation(
    project_uuid: UUID,
    environment_uuid: UUID,
    generation_uuid: UUID,
    deployment_service: Annotated[DeploymentService, Depends(DeploymentService)],
    notes: str | None = None,
) -> DeploymentTable:
    """Deploy a generation to an environment."""
    return deployment_service.deploy_generation(
        environment_uuid, generation_uuid, notes
    )


@environments_router.get(
    "/projects/{project_uuid}/environments/{environment_uuid}/deployment",
    response_model=DeploymentPublic,
)
async def get_active_deployment(
    project_uuid: UUID,
    environment_uuid: UUID,
    deployment_service: Annotated[DeploymentService, Depends(DeploymentService)],
) -> DeploymentTable:
    """Get active deployment for an environment."""
    return deployment_service.get_active_deployment(environment_uuid)


@environments_router.get(
    "/projects/{project_uuid}/environments/{environment_uuid}/generation",
    response_model=GenerationPublic,
)
async def get_environment_generation(
    project_uuid: UUID,
    environment_uuid: UUID,
    deployment_service: Annotated[DeploymentService, Depends(DeploymentService)],
) -> GenerationTable:
    """Get the currently active generation for an environment."""
    return deployment_service.get_generation_for_environment(environment_uuid)


@environments_router.get(
    "/projects/{project_uuid}/environments/{environment_uuid}/history",
    response_model=Sequence[DeploymentPublic],
)
async def get_deployment_history(
    project_uuid: UUID,
    environment_uuid: UUID,
    deployment_service: Annotated[DeploymentService, Depends(DeploymentService)],
) -> Sequence[DeploymentTable]:
    """Get deployment history for an environment."""
    return deployment_service.get_deployment_history(environment_uuid)
