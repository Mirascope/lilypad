"""The auth utils"""

import posthog
from fastapi import HTTPException
from sqlmodel import Session, select

from .....ee.server.models.user_organizations import UserOrganizationTable, UserRole
from ...._utils import create_jwt_token
from ....models import EnvironmentTable, OrganizationTable, UserTable
from ....schemas import OrganizationPublic, UserPublic


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
    organization = OrganizationTable(
        name=f"{name}'s Workspace",
    )
    session.add(organization)
    session.flush()
    organization_public = OrganizationPublic.model_validate(organization)

    # Create default environment
    environment = EnvironmentTable(
        organization_uuid=organization_public.uuid,
        name="Default",
        description="Default environment",
        is_default=True,
    )
    session.add(environment)
    session.flush()

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
