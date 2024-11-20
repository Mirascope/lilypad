"""The `/auth` API router."""

import contextlib
import os
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from fastapi import APIRouter, Request, Response, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from workos import WorkOSClient

from ..._utils import create_jwt_token
from ...models import UserSession

auth_router = APIRouter()

workos = WorkOSClient(api_key=os.getenv("WORKOS_API_KEY"))
client_id = os.getenv("WORKOS_CLIENT_ID")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class LoginType(StrEnum):
    GITHUB_OAUTH = "GitHubOAuth"
    GOOGLE_OAUTH = "GoogleOAuth"


class LoginResponse(BaseModel):
    authorization_url: str


@auth_router.post("/auth/login/{login_type}", response_model=LoginResponse)
async def login(login_type: LoginType) -> LoginResponse:
    try:
        redirect_uri = "http://localhost:5173/auth/callback"
        authorization_url = workos.sso.get_authorization_url(
            provider=login_type.value,
            redirect_uri=redirect_uri,
        )
        return LoginResponse(authorization_url=authorization_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@auth_router.get("/auth/callback", response_model=UserSession)
async def auth_callback(
    code: str, request: Request, response: Response
) -> JSONResponse:
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No authorization code provided",
        )

    try:
        profile_and_token = workos.sso.get_profile_and_token(code)
        profile = profile_and_token.profile
        user_session = UserSession(
            first_name=profile.first_name,
            raw_profile=profile.dict(),
            session_id=profile.id,
            expires_at=str(datetime.now(timezone.utc) + timedelta(days=7)),
        )
        access_token = create_jwt_token(user_session)
        user_session.access_token = access_token
        create_user_payload = {
            "email": profile.email,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
        }
        with contextlib.suppress(Exception):
            user = workos.user_management.create_user(**create_user_payload)
            user_session.id = user.id
        return JSONResponse(
            content=user_session.model_dump(),
            headers=dict(response.headers),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@auth_router.post("/auth/logout")
async def logout(request: Request) -> dict[str, str]:
    request.session.clear()
    return {"message": "Logged out successfully"}


__all__ = ["auth_router"]
