import json
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlmodel import Session, select

from ..db import get_session
from ..models import (
    OrganizationPublic,
    OrganizationTable,
    UserOrganizationTable,
    UserPublic,
    UserRole,
    UserTable,
)
from ..settings import Settings, get_settings

LOCAL_TOKEN = "local-dev-token"


def create_jwt_token(
    user_data: UserPublic,
) -> str:
    settings = get_settings()
    return jwt.encode(
        json.loads(user_data.model_dump_json()),
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


settings = get_settings()
if settings.environment == "local":

    async def oauth2_scheme(token: str | None = None) -> str:  # pyright: ignore[reportRedeclaration]
        return LOCAL_TOKEN

else:
    oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(tokenUrl="token")


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
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserPublic:
    """Dependency to get the current authenticated user from session."""
    """Get the current user from JWT token"""
    if token == LOCAL_TOKEN:
        return await get_local_user(session)
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
                return UserPublic.model_validate(user)
    except (JWTError, KeyError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")
