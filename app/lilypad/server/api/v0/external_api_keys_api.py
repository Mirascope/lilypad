"""ExternalAPIKeyAPI with minimal scope validation."""

from typing import Annotated

from fastapi import APIRouter, Depends

from ..._utils.auth import require_scopes
from ...schemas.external_api_keys import (
    ExternalAPIKeyCreate,
    ExternalAPIKeyPublic,
    ExternalAPIKeyUpdate,
)
from ...schemas.users import UserPublic
from ...services.user_external_api_key_service import UserExternalAPIKeyService

external_api_key_router = APIRouter()


@external_api_key_router.post("/external-api-keys", response_model=ExternalAPIKeyPublic)
async def store_external_api_key(
    request: ExternalAPIKeyCreate,
    user: Annotated[UserPublic, Depends(require_scopes("vault:write"))],
    external_api_key_service: Annotated[
        UserExternalAPIKeyService, Depends(UserExternalAPIKeyService)
    ],
) -> ExternalAPIKeyPublic:
    """Store an external API key for a given service."""
    external_api_key_service.store_api_key(
        request.service_name, request.api_key
    )  # pragma: no cover
    return ExternalAPIKeyPublic(  # pragma: no cover
        service_name=request.service_name, masked_api_key=request.api_key
    )


@external_api_key_router.get(
    "/external-api-keys/{service_name}", response_model=ExternalAPIKeyPublic
)
async def get_external_api_key(
    service_name: str,
    user: Annotated[UserPublic, Depends(require_scopes("vault:read"))],
    external_api_key_service: Annotated[
        UserExternalAPIKeyService, Depends(UserExternalAPIKeyService)
    ],
) -> ExternalAPIKeyPublic:
    """Retrieve an external API key for a given service."""
    api_key = external_api_key_service.get_api_key(service_name)  # pragma: no cover
    return ExternalAPIKeyPublic(
        service_name=service_name, masked_api_key=api_key
    )  # pragma: no cover


@external_api_key_router.patch(
    "/external-api-keys/{service_name}", response_model=ExternalAPIKeyPublic
)
async def update_external_api_key(
    user: Annotated[UserPublic, Depends(require_scopes("vault:write"))],
    service_name: str,
    external_api_key_service: Annotated[
        UserExternalAPIKeyService, Depends(UserExternalAPIKeyService)
    ],
    external_api_key_update: ExternalAPIKeyUpdate,
) -> ExternalAPIKeyPublic:
    """Update users keys."""
    external_api_key_service.update_api_key(  # pragma: no cover
        service_name,
        external_api_key_update.api_key,  # pragma: no cover
    )  # pragma: no cover
    return ExternalAPIKeyPublic(  # pragma: no cover
        service_name=service_name, masked_api_key=external_api_key_update.api_key
    )


@external_api_key_router.delete("/external-api-keys/{service_name}")
async def delete_external_api_key(
    service_name: str,
    user: Annotated[UserPublic, Depends(require_scopes("vault:write"))],
    external_api_key_service: Annotated[
        UserExternalAPIKeyService, Depends(UserExternalAPIKeyService)
    ],
) -> bool:
    """Delete an external API key for a given service."""
    return external_api_key_service.delete_api_key(service_name)  # pragma: no cover


@external_api_key_router.get(
    "/external-api-keys", response_model=list[ExternalAPIKeyPublic]
)
async def list_external_api_keys(
    user: Annotated[UserPublic, Depends(require_scopes("vault:read"))],
    external_api_key_service: Annotated[
        UserExternalAPIKeyService, Depends(UserExternalAPIKeyService)
    ],
) -> list[ExternalAPIKeyPublic]:
    """List all external API keys for the user with masked values."""
    return [  # pragma: no cover
        ExternalAPIKeyPublic(service_name=service_name, masked_api_key=secret)
        for service_name, secret in external_api_key_service.list_api_keys().items()
    ]
