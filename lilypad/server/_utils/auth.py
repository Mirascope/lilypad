import base64
import hashlib
import json
import secrets
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlmodel import Session, select

from ..db import get_session
from ..models import (
    APIKeyTable,
    OrganizationTable,
    UserOrganizationTable,
    UserRole,
    UserTable,
)
from ..schemas.organizations import OrganizationPublic
from ..schemas.users import UserPublic
from ..settings import Settings, get_settings

LOCAL_TOKEN = "local-dev-token"


def create_jwt_token(
    user_data: UserPublic,
) -> str:
    """Create a new JWT token."""
    settings = get_settings()
    return jwt.encode(
        json.loads(user_data.model_dump_json()),
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def create_api_key() -> str:
    """Create a new API key."""
    raw_key = base64.b64encode(secrets.token_bytes(32)).decode("utf-8")
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    return key_hash


settings = get_settings()
if settings.environment == "local":

    async def oauth2_scheme(token: str | None = None) -> str:  # pyright: ignore[reportRedeclaration]
        return LOCAL_TOKEN

else:
    oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(
        tokenUrl="token", auto_error=False
    )
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def validate_api_key_project(
    project_uuid: UUID,
    api_key: str | None,
    session: Session,
    strict: bool = True,
) -> bool:
    """Checks if the API key matches the project UUID."""
    api_key_row = session.exec(
        select(APIKeyTable).where(APIKeyTable.key_hash == api_key)
    ).first()
    if not api_key_row:
        if strict:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user"
            )
        return False
    if project_uuid != api_key_row.project_uuid:
        if strict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Project ID for this API Key. Hint: Check your `LILYPAD_PROJECT_ID environment variable`",
            )
        return False
    return True


async def validate_api_key_project_no_strict(
    project_uuid: UUID,
    api_key: Annotated[str | None, Depends(api_key_header)],
    session: Annotated[Session, Depends(get_session)],
) -> bool:
    return await validate_api_key_project(project_uuid, api_key, session, strict=False)


async def validate_api_key_project_strict(
    project_uuid: UUID,
    api_key: Annotated[str | None, Depends(api_key_header)],
    session: Annotated[Session, Depends(get_session)],
) -> bool:
    return await validate_api_key_project(project_uuid, api_key, session, strict=True)


async def get_local_user(session: Session) -> UserPublic:
    """Get the local user for development

    Create a local user and organization if it does not exist.
    """
    local_email = "local@local.com"
    user = session.exec(select(UserTable).where(UserTable.email == local_email)).first()
    if user:
        return UserPublic.model_validate(user)

    org = OrganizationTable(
        uuid=UUID("123e4567-e89b-12d3-a456-426614174000"), name="Local Organization"
    )
    session.add(org)
    session.flush()
    org_public = OrganizationPublic.model_validate(org)
    user = UserTable(
        email=local_email,
        first_name="Local User",
        active_organization_uuid=org.uuid,
    )
    session.add(user)
    session.flush()
    user_public = UserPublic.model_validate(user)
    user_org = UserOrganizationTable(
        user_uuid=user_public.uuid,
        organization_uuid=org_public.uuid,
        role=UserRole.ADMIN,
    )
    session.add(user_org)
    session.flush()
    return user_public


async def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    api_key: Annotated[str | None, Depends(api_key_header)],
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserPublic:
    """Dependency to get the current authenticated user from session."""
    """Get the current user from JWT token"""
    if token == LOCAL_TOKEN:
        return await get_local_user(session)
    if api_key:
        api_key_row = session.exec(
            select(APIKeyTable).where(APIKeyTable.key_hash == api_key)
        ).first()
        if not api_key_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user"
            )
        user_public = UserPublic.model_validate(api_key_row.user)
        request.state.user = user_public
        return user_public

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        # Refresh session data
        if uuid := payload.get("uuid"):
            user = session.exec(select(UserTable).where(UserTable.uuid == uuid)).first()
            if user:
                user_public = UserPublic.model_validate(user)
                request.state.user = user_public
                return user_public
    except (JWTError, KeyError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")
