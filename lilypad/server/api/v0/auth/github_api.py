"""The `/github` API router."""

from typing import Annotated

import httpx
import posthog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ...._utils.posthog import get_posthog_client
from ....db import get_session
from ....schemas.users import UserPublic
from ....settings import Settings, get_settings
from .utils import handle_user

github_router = APIRouter()


@github_router.get("/github/callback", response_model=UserPublic)
async def github_callback(
    code: str,
    posthog: Annotated[posthog.Posthog, Depends(get_posthog_client)],
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_session)],
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
            name = (
                user_data.get("first_name")
                or user_data.get("name")
                or user_data.get("login")
                or email
            )
            return handle_user(
                name=name,
                email=email,
                last_name=None,
                session=session,
                posthog=posthog,
            )

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=500, detail=f"Error communicating with GitHub: {str(exc)}"
            )
