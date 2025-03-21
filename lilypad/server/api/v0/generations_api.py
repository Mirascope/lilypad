"""The `/generations` API router."""

import hashlib
from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ....ee.server._utils import get_current_environment
from ....ee.server.models.environments import Environment
from ....ee.server.services import DeploymentService
from ..._utils import (
    construct_function,
    validate_api_key_project_no_strict,
    validate_api_key_project_strict,
)
from ...models import (
    GenerationTable,
    GenerationUpdate,
)
from ...schemas import (
    GenerationCreate,
    GenerationPublic,
)
from ...services import (
    GenerationService,
    SpanService,
)

generations_router = APIRouter()


@generations_router.get(
    "/projects/{project_uuid}/generations/name/{generation_name}/version/{version_num}",
    response_model=GenerationPublic,
)
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


@generations_router.post(
    "/projects/{project_uuid}/managed-generations",
    response_model=GenerationPublic,
)
async def create_managed_generation(
    project_uuid: UUID,
    generation_create: GenerationCreate,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> GenerationTable:
    """Create a managed generation."""
    if not generation_create.prompt_template:
        raise HTTPException(
            detail="Prompt template is required.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    generation_create.is_managed = True
    generation_create.code = construct_function(
        generation_create.arg_types or {}, generation_create.name, True
    )

    generation_create.hash = hashlib.sha256(
        generation_create.code.encode("utf-8")
    ).hexdigest()

    if generation := generation_service.check_duplicate_managed_generation(
        project_uuid, generation_create
    ):
        return generation

    generation_create.signature = construct_function(
        generation_create.arg_types or {}, generation_create.name, False
    )
    generation_create.version_num = generation_service.get_next_version(
        project_uuid, generation_create.name
    )
    generations = generation_service.find_generations_by_signature(
        project_uuid, generation_create.signature
    )
    if len(generations) == 0:
        generation_create.is_default = True

    return generation_service.create_record(
        generation_create, project_uuid=project_uuid
    )


@generations_router.get(
    "/projects/{project_uuid}/generations/metadata/names", response_model=Sequence[str]
)
async def get_unique_generation_names(
    project_uuid: UUID,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> Sequence[str]:
    """Get all unique generation names."""
    return generation_service.find_unique_generation_names_by_project_uuid(project_uuid)


@generations_router.get(
    "/projects/{project_uuid}/generations/metadata/names/versions",
    response_model=Sequence[GenerationPublic],
)
async def get_latest_version_unique_generation_names(
    project_uuid: UUID,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> Sequence[GenerationTable]:
    """Get all unique generation names."""
    return generation_service.find_unique_generation_names(project_uuid)


@generations_router.get(
    "/projects/{project_uuid}/generations/hash/{generation_hash}",
    response_model=GenerationPublic,
)
async def get_generation_by_hash(
    match_api_key: Annotated[bool, Depends(validate_api_key_project_strict)],
    project_uuid: UUID,
    generation_hash: str,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> GenerationTable:
    """Get generation by hash."""
    return generation_service.find_record_by_hash(project_uuid, generation_hash)


@generations_router.get(
    "/projects/{project_uuid}/generations", response_model=Sequence[GenerationPublic]
)
async def get_generations(
    project_uuid: UUID,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> Sequence[GenerationTable]:
    """Grab all generations."""
    return generation_service.find_all_records(project_uuid=project_uuid)


@generations_router.get(
    "/projects/{project_uuid}/generations/{generation_uuid}",
    response_model=GenerationPublic,
)
async def get_generation(
    project_uuid: UUID,
    generation_uuid: UUID,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> GenerationTable:
    """Grab generation by UUID."""
    return generation_service.find_record_by_uuid(
        generation_uuid, project_uuid=project_uuid
    )


@generations_router.post(
    "/projects/{project_uuid}/generations", response_model=GenerationPublic
)
async def create_new_generation(
    match_api_key: Annotated[bool, Depends(validate_api_key_project_strict)],
    project_uuid: UUID,
    generation_create: GenerationCreate,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> GenerationTable:
    """Create a new generation version."""
    generation_create = generation_create.model_copy(
        update={
            "project_uuid": project_uuid,
            "version_num": generation_service.get_next_version(
                project_uuid, generation_create.name
            ),
        }
    )
    try:
        return generation_service.find_record_by_hash(
            project_uuid, generation_create.hash
        )
    except HTTPException:
        new_generation = generation_service.create_record(generation_create)
        return new_generation


@generations_router.patch(
    "/projects/{project_uuid}/generations/{generation_uuid}",
    response_model=GenerationPublic,
)
async def update_generation(
    match_api_key: Annotated[bool, Depends(validate_api_key_project_no_strict)],
    project_uuid: UUID,
    generation_uuid: UUID,
    generation_update: GenerationUpdate,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> GenerationTable:
    """Update a generation."""
    return generation_service.update_record_by_uuid(
        generation_uuid,
        generation_update.model_dump(exclude_unset=True),
        project_uuid=project_uuid,
    )


@generations_router.delete(
    "/projects/{project_uuid}/generations/names/{generation_name}"
)
async def archive_generations_by_name(
    project_uuid: UUID,
    generation_name: str,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> bool:
    """Archive a generation by name and delete spans by generation name."""
    try:
        generation_service.archive_record_by_name(project_uuid, generation_name)
        span_service.delete_records_by_generation_name(project_uuid, generation_name)
    except Exception:
        return False
    return True


@generations_router.delete("/projects/{project_uuid}/generations/{generation_uuid}")
async def archive_generation(
    project_uuid: UUID,
    generation_uuid: UUID,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> bool:
    """Archive a generation and delete spans by generation UUID."""
    try:
        generation_service.archive_record_by_uuid(generation_uuid)
        span_service.delete_records_by_generation_uuid(project_uuid, generation_uuid)
    except Exception:
        return False
    return True


__all__ = ["generations_router"]
