"""The `/response_models` API router."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from ..._utils import validate_api_key_project_strict
from ...models.response_models import (
    ResponseModelTable,
)
from ...schemas.response_models import ResponseModelCreate, ResponseModelPublic
from ...services.response_models import ResponseModelService

response_models_router = APIRouter()


@response_models_router.get(
    "/projects/{project_uuid}/response_models/hash/{response_model_hash}/active",
    response_model=ResponseModelPublic,
)
async def get_response_model_active_version_by_hash(
    match_api_key: Annotated[bool, Depends(validate_api_key_project_strict)],
    project_uuid: UUID,
    response_model_hash: str,
    response_model_service: Annotated[
        ResponseModelService, Depends(ResponseModelService)
    ],
) -> ResponseModelTable:
    # Retrieve the active version of the response model by its hash.
    return response_model_service.find_response_model_active_version_by_hash(
        project_uuid, response_model_hash
    )


@response_models_router.patch(
    "/projects/{project_uuid}/response_models/{response_model_uuid}/active",
    response_model=ResponseModelPublic,
)
async def set_active_version(
    project_uuid: UUID,
    response_model_uuid: UUID,
    response_model_service: Annotated[
        ResponseModelService, Depends(ResponseModelService)
    ],
) -> ResponseModelTable:
    """Set active version for response model."""
    new_active_version = response_model_service.find_record_by_uuid(response_model_uuid)
    return response_model_service.change_active_version(
        project_uuid, new_active_version
    )


@response_models_router.post(
    "/projects/{project_uuid}/response_models",
    response_model=ResponseModelPublic,
)
async def create_response_model_version(
    match_api_key: Annotated[bool, Depends(validate_api_key_project_strict)],
    project_uuid: UUID,
    response_model_create: ResponseModelCreate,
    response_model_service: Annotated[
        ResponseModelService, Depends(ResponseModelService)
    ],
) -> ResponseModelTable:
    response_model_create = response_model_create.model_copy(
        update={"project_uuid": project_uuid}
    )

    try:
        return response_model_service.find_response_model_active_version_by_hash(
            project_uuid, response_model_create.hash
        )
    except HTTPException:
        return response_model_service.create_record(response_model_create)


__all__ = ["response_models_router"]
