"""The `/auth` API router."""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from workos import WorkOSClient

from ..._utils import create_jwt_token, get_current_user
from ...models import LoginType, User, UserSession
from ...services import DeviceCodeService

auth_router = APIRouter()

workos = WorkOSClient(api_key=os.getenv("WORKOS_API_KEY"))


class LoginResponse(BaseModel):
    authorization_url: str
    device_code: str | None


@auth_router.post("/auth/login/{login_type}", response_model=LoginResponse)
async def login(
    login_type: LoginType, device_code: str | None = Query(None, alias="deviceCode")
) -> LoginResponse:
    try:
        state = json.dumps({"device_code": device_code}) if device_code else None
        redirect_uri = "http://localhost:5173/auth/callback"
        authorization_url = workos.sso.get_authorization_url(
            provider=login_type.value,
            redirect_uri=redirect_uri,
            state=state,
        )
        return LoginResponse(
            authorization_url=authorization_url, device_code=device_code
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@auth_router.get("/auth/callback", response_model=UserSession)
async def auth_callback(
    code: str,
    device_code_service: Annotated[DeviceCodeService, Depends(DeviceCodeService)],
    device_code: str | None = Query(None, alias="deviceCode"),
) -> UserSession:
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
        try:
            existing_users = workos.user_management.list_users(email=profile.email)
            user = existing_users.data[0] if len(existing_users.data) > 0 else None
            if user:
                organization_memberships = (
                    workos.user_management.list_organization_memberships(
                        user_id=user.id
                    ).data
                )
                organizations = [
                    workos.organizations.get_organization(membership.organization_id)
                    for membership in organization_memberships
                ]

            else:
                org_name = f"{profile.first_name}'s Workspace ({profile.email})"
                organization = workos.organizations.create_organization(name=org_name)
                user = workos.user_management.create_user(
                    email=profile.email,
                    first_name=profile.first_name,
                    last_name=profile.last_name,
                )
                workos.user_management.create_organization_membership(
                    organization_id=organization.id,
                    user_id=user.id,
                )
                organizations = [organization]
            user_session.organization_id = organizations[0].id
            user_session.id = user.id
            user_session.organizations = organizations

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )
        access_token = create_jwt_token(user_session)
        if device_code:
            device_code_service.create_record(device_code, access_token)
        user_session.access_token = access_token
        return user_session
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@auth_router.put("/auth/oraganizations/{organization_id}", response_model=UserSession)
async def update_active_organization(
    organization_id: str, user: Annotated[User, Depends(get_current_user)]
) -> UserSession:
    user_session = UserSession.model_validate(
        {
            **user.model_dump(exclude={"organization_id"}),
            "organization_id": organization_id,
        }
    )
    access_token = create_jwt_token(user_session)
    user_session.access_token = access_token
    return user_session


@auth_router.post("/auth/logout")
async def logout(request: Request) -> dict[str, str]:
    request.session.clear()
    return {"message": "Logged out successfully"}


__all__ = ["auth_router"]
