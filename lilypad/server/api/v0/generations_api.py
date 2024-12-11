"""The `/generations` API router."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from ...models import GenerationCreate, GenerationPublic, GenerationTable
from ...services import GenerationService

generations_router = APIRouter()


@generations_router.get(
    "/projects/{project_uuid}/generations/{generation_uuid}",
    response_model=GenerationPublic,
)
async def get_generation_by_uuid(
    generation_uuid: UUID,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> GenerationTable:
    """Get generation by UUID."""
    return generation_service.find_record_by_uuid(generation_uuid)


@generations_router.get(
    "/projects/{project_uuid}/generations/names", response_model=Sequence[str]
)
async def get_unique_generation_names(
    project_uuid: UUID,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> Sequence[str]:
    """Get all unique generation names."""
    return generation_service.find_unique_generation_names_by_project_uuid(project_uuid)


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
    return generation_service.find_records_by_name(project_uuid, generation_name)


@generations_router.get(
    "/projects/{project_uuid}/generations/hash/{generation_hash}",
    response_model=GenerationPublic,
)
async def get_generation_by_hash(
    project_uuid: UUID,
    generation_hash: str,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> GenerationTable:
    """Get generation by hash."""
    return generation_service.find_record_by_hash(generation_hash)


@generations_router.post(
    "/projects/{project_uuid}/generations", response_model=GenerationPublic
)
async def create_new_generation(
    project_uuid: UUID,
    generation_create: GenerationCreate,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> GenerationTable:
    """Create a new generation version."""
    generation_create = generation_create.model_copy(
        update={"project_uuid": project_uuid}
    )
    try:
        return generation_service.find_record_by_hash(generation_create.hash)
    except HTTPException:
        return generation_service.create_record(generation_create)


__all__ = ["generations_router"]