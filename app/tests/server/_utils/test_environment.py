"""Tests for environment utility functions."""

from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic_core import ValidationError
from sqlmodel import Session

from lilypad.server._utils.environment import get_current_environment
from lilypad.server.models import APIKeyTable, EnvironmentTable


@pytest.mark.asyncio
async def test_get_current_environment_with_api_key(db_session: Session):
    """Test getting environment with valid API key."""
    # Create environment
    env = EnvironmentTable(name="production", organization_uuid=uuid4())
    db_session.add(env)
    db_session.commit()

    # Create API key with environment
    api_key = APIKeyTable(
        key_hash="test-key-hash",
        name="Test Key",
        user_uuid=uuid4(),
        organization_uuid=env.organization_uuid,
        project_uuid=uuid4(),
        environment_uuid=env.uuid,
    )
    db_session.add(api_key)
    db_session.commit()
    db_session.refresh(api_key)  # Refresh to load relationships

    # Get environment
    result = await get_current_environment(api_key="test-key-hash", session=db_session)

    assert result.name == "production"
    assert result.uuid == env.uuid


@pytest.mark.asyncio
async def test_get_current_environment_invalid_api_key(db_session: Session):
    """Test getting environment with invalid API key."""
    # No API key in database
    with pytest.raises(HTTPException) as exc_info:
        await get_current_environment(api_key="non-existent-key", session=db_session)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid user"


@pytest.mark.asyncio
async def test_get_current_environment_no_authentication():
    """Test getting environment without authentication."""
    session = Mock()

    with pytest.raises(HTTPException) as exc_info:
        await get_current_environment(api_key=None, session=session)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated"


@pytest.mark.asyncio
async def test_get_current_environment_api_key_without_environment(db_session: Session):
    """Test getting environment when API key has no environment set."""
    # Create API key without environment
    api_key = APIKeyTable(
        key_hash="test-key-no-env",
        name="Test Key No Env",
        user_uuid=uuid4(),
        organization_uuid=uuid4(),
        project_uuid=uuid4(),
        environment_uuid=None,  # No environment
    )
    db_session.add(api_key)
    db_session.commit()

    # Refresh to get the relationship
    db_session.refresh(api_key)

    # This should fail when trying to validate None
    with pytest.raises(ValidationError):
        await get_current_environment(api_key="test-key-no-env", session=db_session)
