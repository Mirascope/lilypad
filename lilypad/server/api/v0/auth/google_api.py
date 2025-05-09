"""The `/google` API router."""

from typing import Annotated

import httpx
import posthog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ...._utils.posthog import get_posthog_client
from ....db import get_session
from ....schemas.users import UserPublic
from ....services.billing import BillingService
from ....settings import Settings, get_settings
from .utils import handle_user

google_router = APIRouter()


@google_router.get("/google/callback", response_model=UserPublic)
async def google_callback(
    code: str,
    posthog: Annotated[posthog.Posthog, Depends(get_posthog_client)],
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_session)],
    billing_service: Annotated[BillingService, Depends(BillingService)],
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

            # User doesn't exist, create new user and organization
            name = user_data.get("given_name") or user_data.get("name") or email
            last_name = user_data.get("family_name") or ""

            return handle_user(
                name=name,
                email=email,
                last_name=last_name,
                session=session,
                posthog=posthog,
                billing_service=billing_service
            )

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=500, detail=f"Error communicating with Google: {str(exc)}"
            )
