"""API endpoints for generations."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from ee import Tier
from lilypad.ee.server.services import GenerationService
from lilypad.server.models import GenerationTable
from lilypad.server.schemas import GenerationPublic

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
