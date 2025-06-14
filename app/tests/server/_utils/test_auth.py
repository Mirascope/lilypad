"""Tests for auth utility functions."""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, Request
from jose import jwt
from sqlmodel import Session

from lilypad.server._utils.auth import (
    DEFAULT_SCOPES,
    create_api_key,
    create_jwt_token,
    get_current_user,
    require_scopes,
    validate_api_key_project,
    validate_api_key_project_no_strict,
    validate_api_key_project_strict,
)
from lilypad.server.models import APIKeyTable, UserTable
from lilypad.server.schemas.users import UserPublic
from lilypad.server.settings import Settings


@pytest.fixture
def mock_settings():
    """Mock settings."""
    settings = Mock(spec=Settings)
    settings.jwt_secret = "test_secret"
    settings.jwt_algorithm = "HS256"
    return settings


@pytest.fixture
def mock_session():
    """Mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def mock_request():
    """Mock request object."""
    request = Mock(spec=Request)
    request.state = Mock()
    return request


@pytest.fixture
def sample_user():
    """Sample user for testing."""
    return UserPublic(
        uuid=uuid4(),
        email="test@example.com",
        first_name="Test",
        last_name="User",
        active_organization_uuid=uuid4(),
    )


def test_create_jwt_token(sample_user, mock_settings):
    """Test JWT token creation."""
    with patch("lilypad.server._utils.auth.get_settings", return_value=mock_settings):
        token = create_jwt_token(sample_user)

        # Decode the token to verify its contents
        decoded = jwt.decode(
            token, mock_settings.jwt_secret, algorithms=[mock_settings.jwt_algorithm]
        )

        assert decoded["email"] == sample_user.email
        assert decoded["first_name"] == sample_user.first_name
        assert decoded["scopes"] == DEFAULT_SCOPES
        assert decoded["uuid"] == str(sample_user.uuid)


def test_create_api_key():
    """Test API key creation."""
    # Mock the random generation
    test_bytes = b"test_random_bytes_for_api_key_12"
    with patch("secrets.token_bytes", return_value=test_bytes):
        key_hash = create_api_key()

        # Verify it's a proper SHA256 hash
        assert len(key_hash) == 64  # SHA256 produces 64 hex characters
        assert all(c in "0123456789abcdef" for c in key_hash)


def test_create_api_key_uniqueness():
    """Test that create_api_key generates unique keys."""
    keys = set()
    for _ in range(10):
        key = create_api_key()
        assert key not in keys
        keys.add(key)


@pytest.mark.asyncio
async def test_validate_api_key_project_success(mock_session):
    """Test successful API key validation."""
    project_uuid = uuid4()
    api_key = "test_api_key"

    # Mock API key in database
    mock_api_key = Mock(spec=APIKeyTable)
    mock_api_key.project_uuid = project_uuid

    mock_result = Mock()
    mock_result.first.return_value = mock_api_key
    mock_session.exec.return_value = mock_result

    result = await validate_api_key_project(project_uuid, api_key, mock_session)
    assert result is True


@pytest.mark.asyncio
async def test_validate_api_key_project_invalid_key_strict(mock_session):
    """Test API key validation with invalid key (strict mode)."""
    project_uuid = uuid4()
    api_key = "invalid_api_key"

    # Mock no API key found
    mock_result = Mock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await validate_api_key_project(project_uuid, api_key, mock_session, strict=True)

    assert exc_info.value.status_code == 401
    assert "Invalid user" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_validate_api_key_project_invalid_key_no_strict(mock_session):
    """Test API key validation with invalid key (non-strict mode)."""
    project_uuid = uuid4()
    api_key = "invalid_api_key"

    # Mock no API key found
    mock_result = Mock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    result = await validate_api_key_project(
        project_uuid, api_key, mock_session, strict=False
    )
    assert result is False


@pytest.mark.asyncio
async def test_validate_api_key_project_wrong_project_strict(mock_session):
    """Test API key validation with wrong project UUID (strict mode)."""
    project_uuid = uuid4()
    wrong_project_uuid = uuid4()
    api_key = "test_api_key"

    # Mock API key with different project UUID
    mock_api_key = Mock(spec=APIKeyTable)
    mock_api_key.project_uuid = wrong_project_uuid

    mock_result = Mock()
    mock_result.first.return_value = mock_api_key
    mock_session.exec.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await validate_api_key_project(project_uuid, api_key, mock_session, strict=True)

    assert exc_info.value.status_code == 400
    assert "Invalid Project ID" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_validate_api_key_project_wrong_project_no_strict(mock_session):
    """Test API key validation with wrong project UUID (non-strict mode)."""
    project_uuid = uuid4()
    wrong_project_uuid = uuid4()
    api_key = "test_api_key"

    # Mock API key with different project UUID
    mock_api_key = Mock(spec=APIKeyTable)
    mock_api_key.project_uuid = wrong_project_uuid

    mock_result = Mock()
    mock_result.first.return_value = mock_api_key
    mock_session.exec.return_value = mock_result

    result = await validate_api_key_project(
        project_uuid, api_key, mock_session, strict=False
    )
    assert result is False


@pytest.mark.asyncio
async def test_validate_api_key_project_no_strict_wrapper(mock_session):
    """Test validate_api_key_project_no_strict wrapper."""
    project_uuid = uuid4()
    api_key = "test_api_key"

    with patch("lilypad.server._utils.auth.validate_api_key_project") as mock_validate:
        mock_validate.return_value = True

        result = await validate_api_key_project_no_strict(
            project_uuid, api_key, mock_session
        )

        assert result is True
        mock_validate.assert_called_once_with(
            project_uuid, api_key, mock_session, strict=False
        )


@pytest.mark.asyncio
async def test_validate_api_key_project_strict_wrapper(mock_session):
    """Test validate_api_key_project_strict wrapper."""
    project_uuid = uuid4()
    api_key = "test_api_key"

    with patch("lilypad.server._utils.auth.validate_api_key_project") as mock_validate:
        mock_validate.return_value = True

        result = await validate_api_key_project_strict(
            project_uuid, api_key, mock_session
        )

        assert result is True
        mock_validate.assert_called_once_with(
            project_uuid, api_key, mock_session, strict=True
        )


@pytest.mark.asyncio
async def test_get_current_user_with_api_key(mock_request, mock_session, mock_settings):
    """Test getting current user with API key."""
    api_key = "test_api_key"
    user_uuid = uuid4()

    # Mock user and API key
    mock_user = Mock(spec=UserTable)
    mock_user.uuid = user_uuid
    mock_user.email = "test@example.com"
    mock_user.first_name = "Test"
    mock_user.last_name = "User"
    mock_user.active_organization_uuid = uuid4()
    mock_user.keys = {}
    mock_user.user_organizations = []
    mock_user.user_consents = None

    mock_api_key = Mock(spec=APIKeyTable)
    mock_api_key.user = mock_user

    mock_result = Mock()
    mock_result.first.return_value = mock_api_key
    mock_session.exec.return_value = mock_result

    result = await get_current_user(
        request=mock_request,
        token=None,  # type: ignore[arg-type]
        api_key=api_key,
        session=mock_session,
        settings=mock_settings,
    )

    assert result.email == "test@example.com"
    assert result.scopes == DEFAULT_SCOPES
    assert mock_request.state.user == result


@pytest.mark.asyncio
async def test_get_current_user_with_invalid_api_key(
    mock_request, mock_session, mock_settings
):
    """Test getting current user with invalid API key."""
    api_key = "invalid_api_key"

    # Mock no API key found
    mock_result = Mock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            request=mock_request,
            token=None,  # type: ignore[arg-type]
            api_key=api_key,
            session=mock_session,
            settings=mock_settings,
        )

    assert exc_info.value.status_code == 401
    assert "Invalid user" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_user_with_jwt_token(
    mock_request, mock_session, mock_settings, sample_user
):
    """Test getting current user with JWT token."""
    # Create a valid JWT token
    token_payload = {
        "uuid": str(sample_user.uuid),
        "email": sample_user.email,
        "first_name": sample_user.first_name,
        "scopes": ["custom:scope"],
    }
    token = jwt.encode(
        token_payload, mock_settings.jwt_secret, algorithm=mock_settings.jwt_algorithm
    )

    # Mock user in database
    mock_user = Mock(spec=UserTable)
    mock_user.uuid = sample_user.uuid
    mock_user.email = sample_user.email
    mock_user.first_name = sample_user.first_name
    mock_user.last_name = sample_user.last_name
    mock_user.active_organization_uuid = sample_user.active_organization_uuid
    mock_user.keys = {}
    mock_user.user_organizations = []
    mock_user.user_consents = None

    mock_result = Mock()
    mock_result.first.return_value = mock_user
    mock_session.exec.return_value = mock_result

    result = await get_current_user(
        request=mock_request,
        token=token,
        api_key=None,
        session=mock_session,
        settings=mock_settings,
    )

    assert result.email == sample_user.email
    assert result.scopes == ["custom:scope"]
    assert mock_request.state.user == result


@pytest.mark.asyncio
async def test_get_current_user_with_invalid_jwt(
    mock_request, mock_session, mock_settings
):
    """Test getting current user with invalid JWT token."""
    # Create an invalid token
    token = "invalid.jwt.token"

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            request=mock_request,
            token=token,
            api_key=None,
            session=mock_session,
            settings=mock_settings,
        )

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_no_authentication(
    mock_request, mock_session, mock_settings
):
    """Test getting current user with no authentication."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            request=mock_request,
            token=None,  # type: ignore[arg-type]
            api_key=None,
            session=mock_session,
            settings=mock_settings,
        )

    assert exc_info.value.status_code == 401
    assert "Not authenticated" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_user_jwt_user_not_found(
    mock_request, mock_session, mock_settings
):
    """Test getting current user when JWT is valid but user not in database."""
    # Create a valid JWT token
    token_payload = {
        "uuid": str(uuid4()),
        "email": "nonexistent@example.com",
        "scopes": DEFAULT_SCOPES,
    }
    token = jwt.encode(
        token_payload, mock_settings.jwt_secret, algorithm=mock_settings.jwt_algorithm
    )

    # Mock no user found in database
    mock_result = Mock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            request=mock_request,
            token=token,
            api_key=None,
            session=mock_session,
            settings=mock_settings,
        )

    assert exc_info.value.status_code == 401
    assert "Invalid user" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_require_scopes_success():
    """Test require_scopes with sufficient permissions."""
    user = UserPublic(
        uuid=uuid4(),
        email="test@example.com",
        first_name="Test",
        last_name="User",
        active_organization_uuid=uuid4(),
        scopes=["user:read", "user:write", "admin:read"],
    )

    # Create validator for required scopes
    validator = require_scopes("user:read", "user:write")

    # Should not raise exception
    result = await validator(user)
    assert result == user


@pytest.mark.asyncio
async def test_require_scopes_missing_scopes():
    """Test require_scopes with missing permissions."""
    user = UserPublic(
        uuid=uuid4(),
        email="test@example.com",
        first_name="Test",
        last_name="User",
        active_organization_uuid=uuid4(),
        scopes=["user:read"],
    )

    # Create validator requiring scopes the user doesn't have
    validator = require_scopes("user:write", "admin:read")

    with pytest.raises(HTTPException) as exc_info:
        await validator(user)

    assert exc_info.value.status_code == 403
    assert "Missing scopes" in str(exc_info.value.detail)
    assert "user:write" in str(exc_info.value.detail)
    assert "admin:read" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_require_scopes_no_scopes_attribute():
    """Test require_scopes when user has no scopes attribute."""
    user = UserPublic(
        uuid=uuid4(),
        email="test@example.com",
        first_name="Test",
        last_name="User",
        active_organization_uuid=uuid4(),
    )
    # Remove scopes attribute
    if hasattr(user, "scopes"):
        delattr(user, "scopes")

    # Create validator for default scopes
    validator = require_scopes("user:read")

    # Should set default scopes and validate
    result = await validator(user)
    assert result.scopes == DEFAULT_SCOPES


@pytest.mark.asyncio
async def test_require_scopes_none_scopes():
    """Test require_scopes when user scopes is None."""
    user = UserPublic(
        uuid=uuid4(),
        email="test@example.com",
        first_name="Test",
        last_name="User",
        active_organization_uuid=uuid4(),
    )
    # Manually set scopes to None after creation
    user.scopes = None  # type: ignore[assignment]

    # Create validator for default scopes
    validator = require_scopes("user:read")

    # Should set default scopes and validate
    result = await validator(user)
    assert result.scopes == DEFAULT_SCOPES


@pytest.mark.asyncio
async def test_require_scopes_empty_required():
    """Test require_scopes with no required scopes."""
    user = UserPublic(
        uuid=uuid4(),
        email="test@example.com",
        first_name="Test",
        last_name="User",
        active_organization_uuid=uuid4(),
        scopes=[],
    )

    # Create validator with no required scopes
    validator = require_scopes()

    # Should always pass
    result = await validator(user)
    assert result == user
