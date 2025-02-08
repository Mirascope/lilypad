"""The `/github` API router."""

from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from ...._utils import create_jwt_token
from ....db import get_session
from ....models import (
    OrganizationTable,
    UserOrganizationTable,
    UserRole,
    UserTable,
)
from ....schemas import OrganizationPublic, UserPublic
from ....services import DeviceCodeService
from ....settings import Settings, get_settings

github_router = APIRouter()


@github_router.get("/github/callback", response_model=UserPublic)
async def github_callback(
    code: str,
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_session)],
    device_code_service: Annotated[DeviceCodeService, Depends(DeviceCodeService)],
    device_code: str | None = Query(None, alias="deviceCode"),
) -> UserPublic:
    """Callback for GitHub OAuth.

    Saves the user and organization or retrieves the user after authenticating
    with GitHub.
    """
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No authorization code provided",
        )
    async with httpx.AsyncClient() as client:
        try:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                json={
                    "client_id": settings.github_client_id,
                    "client_secret": settings.github_client_secret,
                    "code": code,
                    "redirect_uri": f"{settings.client_url}/auth/callback",
                },
                headers={"Accept": "application/json"},
            )
            token_data = token_response.json()
            if "error" in token_data:
                raise HTTPException(
                    status_code=400, detail=f"GitHub OAuth error: {token_data['error']}"
                )

            access_token = token_data["access_token"]
            user_response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            user_data: dict = user_response.json()
            email = user_data.get("email")
            if not email:
                user_email_response = await client.get(
                    "https://api.github.com/user/emails",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                    },
                )
                user_emails: list[dict] = user_email_response.json()
                if len(user_emails) > 0:
                    for user_email in user_emails:
                        if user_email.get("primary"):
                            email = user_email.get("email")
                            break
                    if not email:  # Fall back to the first email if no primary email
                        email = user_emails[0].get("email")
            if not email:
                raise HTTPException(
                    status_code=400, detail="No email address found in GitHub account"
                )
            user = session.exec(
                select(UserTable).where(UserTable.email == email)
            ).first()
            if user:
                user_public = UserPublic.model_validate(user)
                lilypad_token = create_jwt_token(user_public)
                user_public = user_public.model_copy(
                    update={"access_token": lilypad_token}
                )
                if device_code:
                    device_code_service.create_record(device_code, lilypad_token)
                return user_public
            organization = OrganizationTable(
                name=f"{user_data['name']}'s Workspace",
            )
            session.add(organization)
            session.flush()
            organization_public = OrganizationPublic.model_validate(organization)
            user = UserTable(
                email=email,
                first_name=user_data.get("first_name") or user_data.get("name", ""),
                last_name=user_data.get("last_name", ""),
                active_organization_uuid=organization_public.uuid,
            )
            session.add(user)
            session.flush()
            if not user.uuid:
                raise HTTPException(
                    status_code=500, detail="User creation failed, please try again"
                )
            user_organization = UserOrganizationTable(
                user_uuid=user.uuid,
                organization_uuid=organization_public.uuid,
                role=UserRole.OWNER,
            )
            session.add(user_organization)
            session.flush()
            user_public = UserPublic.model_validate(user)

            lilypad_token = create_jwt_token(user_public)
            user_public = user_public.model_copy(update={"access_token": lilypad_token})
            if device_code:
                device_code_service.create_record(device_code, lilypad_token)
            return user_public

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=500, detail=f"Error communicating with GitHub: {str(exc)}"
            )
