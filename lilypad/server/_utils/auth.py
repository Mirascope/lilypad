import os
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from workos import WorkOSClient

from ..models import User, UserSession
from ..settings import Settings, get_settings

workos = WorkOSClient(api_key=os.getenv("WORKOS_API_KEY"))


def create_jwt_token(
    user_data: UserSession,
) -> str:
    settings = get_settings()
    return jwt.encode(
        {**user_data.model_dump()},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


if os.getenv("LILYPAD_LOCAL", "false").lower() == "true":

    async def oauth2_scheme(token: str | None = None) -> str:  # pyright: ignore[reportRedeclaration]
        return "local-dev-token"
else:
    oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """Dependency to get the current authenticated user from session."""
    """Get the current user from JWT token"""
    if token == "local-dev-token":
        return User(
            id="local",
            organization_id="local",
            raw_profile={},
            session_id="local",
            first_name="Local User",
            expires_at="",
        )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        # Refresh session data
        if payload.get("id"):
            return User(**payload)
        email = payload.get("email")
        users = workos.user_management.list_users(email=email)
        if not users or not users.data or len(users.data) < 1:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        user = users.data[0]
        payload["id"] = user.id
        return User(**payload)

    except (JWTError, KeyError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
