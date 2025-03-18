"""Secrets API with minimal scope validation."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from ..._utils.auth import require_scopes
from ...schemas import UserPublic
from ...schemas.secrets import SecretCreate, SecretPublic
from ...services.user_secret_service import UserSecretService

secrets_router = APIRouter()


@secrets_router.post("", response_model=SecretPublic)
async def store_secret(
    request: SecretCreate,
    user: Annotated[UserPublic, Depends(require_scopes("vault:write"))],
    secret_service: Annotated[UserSecretService, Depends(UserSecretService)],
) -> SecretPublic:
    """Store an API key for a service."""
    if not secret_service.update_api_key(request.service_name, request.api_key):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store secret.",
        )

    return SecretPublic(service_name=request.service_name, api_key=request.api_key)


@secrets_router.get("/{service_name}", response_model=SecretPublic)
async def get_secret(
    service_name: str,
    user: Annotated[UserPublic, Depends(require_scopes("vault:read"))],
    secret_service: Annotated[UserSecretService, Depends(UserSecretService)],
) -> SecretPublic:
    """Get a partially masked API key for a service."""
    api_key = secret_service.get_api_key(service_name)
    return SecretPublic(service_name=service_name, api_key=api_key)


@secrets_router.delete("/{service_name}", response_model=SecretPublic)
async def delete_secret(
    service_name: str,
    user: Annotated[UserPublic, Depends(require_scopes("vault:write"))],
    secret_service: Annotated[UserSecretService, Depends(UserSecretService)],
) -> SecretPublic:
    """Delete an API key for a service."""
    if not secret_service.delete_api_key(service_name):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete secret.",
        )
    return SecretPublic(service_name=service_name, api_key="")


@secrets_router.get("", response_model=dict[str, str])
async def list_secrets(
    user: Annotated[UserPublic, Depends(require_scopes("vault:read"))],
    secret_service: Annotated[UserSecretService, Depends(UserSecretService)],
) -> dict[str, str]:
    """List all available services with stored API keys."""
    user_data = secret_service.get_user()
    return dict.fromkeys(user_data.keys.keys(), "********")
