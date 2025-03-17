from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlmodel import Session, select
from starlette import status
from starlette.requests import Request

from lilypad.ee.server.models.environments import Environment, EnvironmentTable
from lilypad.server._utils.auth import LOCAL_TOKEN, api_key_header, oauth2_scheme
from lilypad.server.db import get_session
from lilypad.server.models import APIKeyTable, OrganizationTable


def get_local_environment(session: Session, project_uuid: str) -> Environment:
    """Get the local environment."""
    environment = session.exec(
        select(EnvironmentTable).where(EnvironmentTable.name == "local")
    ).first()
    if environment:
        return Environment.model_validate(environment)

    org = OrganizationTable(
        uuid=UUID("123e4567-e89b-12d3-a456-426614174000"), name="Local Organization"
    )
    environment = EnvironmentTable(
        name="local",
        organization_uuid=org.uuid,  # pyright: ignore [reportArgumentType]
        project_uuid=UUID(project_uuid),
    )
    session.add(environment)
    session.flush()

    return Environment.model_validate(environment)


async def get_current_environment(
    request: Request,
    api_key: Annotated[str | None, Depends(api_key_header)],
    token: Annotated[str | None, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_session)],
) -> Environment:
    """Get current environment based on authentication method."""
    if token == LOCAL_TOKEN:
        project_uuid = request.path_params["project_uuid"]
        if not project_uuid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Project UUID required"
            )
        return get_local_environment(session, project_uuid)
    if api_key:
        api_key_row = session.exec(
            select(APIKeyTable).where(APIKeyTable.key_hash == api_key)
        ).first()
        if not api_key_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user"
            )
        return Environment.model_validate(api_key_row.environment)
    elif token:
        raise HTTPException(status_code=401, detail="This endpoint requires an API key")
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")
