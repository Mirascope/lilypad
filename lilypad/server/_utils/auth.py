import os
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyCookie, OAuth2PasswordBearer
from jose import JWTError, jwt
from workos import WorkOSClient

from ..models import User, UserSession

workos = WorkOSClient(api_key=os.getenv("WORKOS_API_KEY"))
COOKIE_NAME = "session_token"
SESSION_EXPIRE_MINUTES = 60 * 24  # 24 hours
JWT_SECRET = os.getenv("JWT_SECRET") or "my-secret-key"
ALGORITHM = "HS256"
cookie_scheme = APIKeyCookie(name=COOKIE_NAME, auto_error=False)


def create_jwt_token(user_data: UserSession) -> str:
    return jwt.encode({**user_data.model_dump()}, JWT_SECRET, algorithm=ALGORITHM)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """Dependency to get the current authenticated user from session."""
    """Get the current user from either session or JWT token"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
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
        request.session.update(payload)
        return User(**payload)

    except (JWTError, KeyError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
