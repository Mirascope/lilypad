"""The auth utils"""

import posthog
from fastapi import HTTPException
from sqlmodel import Session, select

from ...._utils import create_jwt_token
from ....models import UserTable
from ....schemas.users import UserPublic


def handle_user(
    name: str,
    email: str,
    last_name: str | None,
    session: Session,
    posthog: posthog.Posthog,
) -> UserPublic:
    """Handle user creation or retrieval."""
    user = session.exec(select(UserTable).where(UserTable.email == email)).first()

    if user:
        user_public = UserPublic.model_validate(user)
        lilypad_token = create_jwt_token(user_public)
        user_public = user_public.model_copy(update={"access_token": lilypad_token})
        return user_public

    # Create organization for new user
    return create_new_user(
        name=name,
        email=email,
        last_name=last_name,
        session=session,
        posthog=posthog,
    )


def create_new_user(
    name: str,
    email: str,
    last_name: str | None,
    session: Session,
    posthog: posthog.Posthog,
) -> UserPublic:
    """Create a new user and organization."""
    # Create new user
    user = UserTable(
        email=email,
        first_name=name,
        last_name=last_name,
        active_organization_uuid=None,
    )
    session.add(user)
    session.flush()

    if not user.uuid:
        raise HTTPException(
            status_code=500, detail="User creation failed, please try again"
        )

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
