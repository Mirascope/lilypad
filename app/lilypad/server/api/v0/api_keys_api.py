"""The `/api-keys` API router."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ..._utils import create_api_key
from ...models.api_keys import APIKeyTable
from ...schemas.api_keys import APIKeyCreate, APIKeyPublic
from ...services import APIKeyService, EnvironmentService

api_keys_api = APIRouter()


@api_keys_api.get(
    "/api-keys",
    response_model=Sequence[APIKeyPublic],
)
async def get_api_keys(
    api_key_service: Annotated[APIKeyService, Depends(APIKeyService)],
) -> Sequence[APIKeyTable]:
    """Get an API keys."""
    return api_key_service.find_all_records()


@api_keys_api.post("/api-keys", response_model=str)
async def post_api_key(
    api_key_create: APIKeyCreate,
    api_key_service: Annotated[APIKeyService, Depends(APIKeyService)],
    environment_service: Annotated[EnvironmentService, Depends(EnvironmentService)],
) -> str:
    """Create an API key and returns the full key."""
    environment = environment_service.find_record_by_uuid(
        api_key_create.environment_uuid
    )
    api_key, key_hash = create_api_key(environment.name)
    api_key_create.key_hash = key_hash
    record = api_key_service.create_record(api_key_create)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to create API key",
        )
    return api_key


@api_keys_api.delete("/api-keys/{api_key_uuid}")
async def delete_api_key(
    api_key_uuid: UUID,
    api_key_service: Annotated[APIKeyService, Depends(APIKeyService)],
) -> bool:
    """Delete an API key."""
    return api_key_service.delete_record_by_uuid(api_key_uuid)
