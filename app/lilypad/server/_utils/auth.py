"""Auth utilities for Lilypad server."""

import base64
import hashlib
import json
import secrets
from collections.abc import Callable, Coroutine
from datetime import datetime, timezone
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from pydantic import ValidationError
from sqlmodel import Session, select

from ..db import get_session
from ..models import (
    APIKeyTable,
    UserTable,
)
from ..schemas.users import UserPublic
from ..settings import Settings, get_settings

LOCAL_TOKEN = "local-dev-token"


# Default scopes for all users
DEFAULT_SCOPES = ["user:read", "user:write", "vault:read", "vault:write"]


def create_jwt_token(
    user_data: UserPublic,
) -> str:
    """Create a JWT token with default scopes for all users."""
    settings = get_settings()
    from jose import jwt

    user_dict = json.loads(user_data.model_dump_json())
    user_dict["scopes"] = DEFAULT_SCOPES

    return jwt.encode(
        user_dict,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def create_api_key(prefix: str) -> tuple[str, str]:
    """Create a new API key."""
    raw_key = base64.b64encode(secrets.token_bytes(32)).decode("utf-8")
    api_key = f"lp_{prefix[:7].lower()}_{raw_key}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    return api_key, key_hash


settings = get_settings()
oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(
    tokenUrl="token", auto_error=False
)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def validate_api_key_project(
    project_uuid: UUID,
    api_key: str | None,
    session: Session,
    strict: bool = True,
) -> APIKeyTable | None:
    """Checks if the API key matches the project UUID."""
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest() if api_key else None
    api_key_row = session.exec(
        select(APIKeyTable).where(APIKeyTable.key_hash == api_key_hash)
    ).first()
    if not api_key_row:
        if strict:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user"
            )
        return api_key_row
    if project_uuid != api_key_row.project_uuid:
        if strict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Project ID for this API Key. Hint: Check your `LILYPAD_PROJECT_ID environment variable`",
            )
        return None
    return api_key_row


async def validate_api_key_project_no_strict(
    project_uuid: UUID,
    api_key: Annotated[str | None, Depends(api_key_header)],
    session: Annotated[Session, Depends(get_session)],
) -> APIKeyTable | None:
    return await validate_api_key_project(project_uuid, api_key, session, strict=False)


async def validate_api_key_project_strict(
    project_uuid: UUID,
    api_key: Annotated[str | None, Depends(api_key_header)],
    session: Annotated[Session, Depends(get_session)],
) -> APIKeyTable | None:
    return await validate_api_key_project(project_uuid, api_key, session, strict=True)


async def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    api_key: Annotated[str | None, Depends(api_key_header)],
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserPublic:
    """Dependency to get the current authenticated user from session."""
    """Get the current user from JWT token"""
    if api_key:
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        api_key_row = session.exec(
            select(APIKeyTable).where(APIKeyTable.key_hash == api_key_hash)
        ).first()
        if not api_key_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user"
            )

        if api_key_row.expires_at and api_key_row.expires_at < datetime.now(
            timezone.utc
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="API key has expired"
            )

        user_public = UserPublic.model_validate(api_key_row.user)
        user_public.scopes = DEFAULT_SCOPES  # type: ignore[misc]
        request.state.user = user_public
        return user_public

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    from jose import JWTError, jwt

    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        # Refresh session data
        if uuid := payload.get("uuid"):
            user = session.exec(select(UserTable).where(UserTable.uuid == uuid)).first()
            if user:
                user_public = UserPublic.model_validate(user)
                user_public.scopes = payload.get("scopes", DEFAULT_SCOPES)  # type: ignore[misc]
                request.state.user = user_public
                return user_public
    except (JWTError, KeyError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")


def require_scopes(
    *required_scopes: str,
) -> Callable[[UserPublic], Coroutine[Any, Any, Any]]:
    """Create a dependency that requires specific scopes."""

    async def validate_scopes(
        user: Annotated[UserPublic, Depends(get_current_user)],
    ) -> UserPublic:
        if not hasattr(user, "scopes") or user.scopes is None:
            user.scopes = DEFAULT_SCOPES  # type: ignore[misc]

        missing_scopes = [
            scope for scope in required_scopes if scope not in user.scopes
        ]
        if missing_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Missing scopes: {', '.join(missing_scopes)}",
            )

        return user

    return validate_scopes
