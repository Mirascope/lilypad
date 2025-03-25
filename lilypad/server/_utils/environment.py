from typing import Annotated

from fastapi import Depends, HTTPException
from sqlmodel import Session, select
from starlette import status

from lilypad.server._utils.auth import api_key_header
from lilypad.server.db import get_session

from ..models import APIKeyTable
from ..models.environments import Environment


async def get_current_environment(
    api_key: Annotated[str | None, Depends(api_key_header)],
    session: Annotated[Session, Depends(get_session)],
) -> Environment:
    """Get current environment based on authentication method."""
    if api_key:
        api_key_row = session.exec(
            select(APIKeyTable).where(APIKeyTable.key_hash == api_key)
        ).first()
        if not api_key_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user"
            )
        return Environment.model_validate(api_key_row.environment)
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")
