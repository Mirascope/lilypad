"""The `/google` API router."""

from typing import Annotated

import httpx
import posthog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ...._utils import create_jwt_token
from ...._utils.posthog import get_posthog_client
from ....db import get_session
from ....models import (
    OrganizationTable,
    UserOrganizationTable,
    UserRole,
    UserTable,
)
from ....schemas import OrganizationPublic, UserPublic
from ....settings import Settings, get_settings

google_router = APIRouter()


@google_router.get("/google/callback", response_model=UserPublic)
async def google_callback(
    code: str,
    posthog: Annotated[posthog.Posthog, Depends(get_posthog_client)],
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_session)],
) -> UserPublic:
    """Callback for Google OAuth.

    Saves the user and organization or retrieves the user after authenticating
    with Google.
    """
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No authorization code provided",
        )
    async with httpx.AsyncClient() as client:
        try:
            # Exchange the authorization code for an access token
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "code": code,
                    "redirect_uri": f"{settings.client_url}/auth/callback",
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )
            token_data = token_response.json()
            if "error" in token_data:
                raise HTTPException(
                    status_code=400, detail=f"Google OAuth error: {token_data['error']}"
                )

            access_token = token_data["access_token"]

            # Get user information using the access token
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            user_data: dict = user_response.json()

            # Extract email (which is required for Google accounts)
            email = user_data.get("email")
            if not email:
                raise HTTPException(
                    status_code=400, detail="No email address found in Google account"
                )

            # Check if email is verified
            email_verified = user_data.get("verified_email", False)
            if not email_verified:
                raise HTTPException(
                    status_code=400, detail="Email address is not verified"
                )

            # Check if user already exists
            user = session.exec(
                select(UserTable).where(UserTable.email == email)
            ).first()

            if user:
                # User exists, return user data with new access token
                user_public = UserPublic.model_validate(user)
                lilypad_token = create_jwt_token(user_public)
                user_public = user_public.model_copy(
                    update={"access_token": lilypad_token}
                )
                return user_public

            # User doesn't exist, create new user and organization
            name = user_data.get("given_name") or user_data.get("name") or email
            last_name = user_data.get("family_name") or ""

            # Create organization for new user
            organization = OrganizationTable(
                name=f"{name}'s Workspace",
            )
            session.add(organization)
            session.flush()
            organization_public = OrganizationPublic.model_validate(organization)

            # Create new user
            user = UserTable(
                email=email,
                first_name=name,
                last_name=last_name,
                active_organization_uuid=organization_public.uuid,
            )
            session.add(user)
            session.flush()

            if not user.uuid:
                raise HTTPException(
                    status_code=500, detail="User creation failed, please try again"
                )

            # Create user-organization relationship
            user_organization = UserOrganizationTable(
                user_uuid=user.uuid,
                organization_uuid=organization_public.uuid,
                role=UserRole.OWNER,
            )
            session.add(user_organization)
            session.flush()

            # Generate JWT token for new user
            user_public = UserPublic.model_validate(user)
            lilypad_token = create_jwt_token(user_public)
            user_public = user_public.model_copy(update={"access_token": lilypad_token})

            # Track sign up event
            posthog.capture(
                distinct_id=user_public.email,
                event="sign_up",
            )

            return user_public

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=500, detail=f"Error communicating with Google: {str(exc)}"
            )
