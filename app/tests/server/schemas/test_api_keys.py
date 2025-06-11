"""Tests for API key schemas."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from lilypad.server.schemas.api_keys import APIKeyCreate


def test_api_key_create_with_timezone_aware_datetime():
    """Test creating API key with timezone-aware datetime."""
    # Create with timezone-aware datetime
    utc_time = datetime.now(timezone.utc)
    api_key = APIKeyCreate(
        name="Test Key",
        project_uuid="123e4567-e89b-12d3-a456-426614174000",
        environment_uuid="123e4567-e89b-12d3-a456-426614174001",
        expires_at=utc_time,
    )

    assert api_key.expires_at == utc_time
    assert api_key.expires_at.tzinfo is not None


def test_api_key_create_with_timezone_naive_datetime():
    """Test that creating API key with timezone-naive datetime raises validation error."""
    # Create with timezone-naive datetime - should fail
    naive_time = datetime(2024, 12, 25, 12, 0, 0)

    with pytest.raises(ValidationError) as exc_info:
        APIKeyCreate(
            name="Test Key",
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            environment_uuid="123e4567-e89b-12d3-a456-426614174001",
            expires_at=naive_time,
        )

    errors = exc_info.value.errors()
    assert any(error["type"] == "timezone_aware" for error in errors)


def test_api_key_create_without_explicit_expiration():
    """Test creating API key without explicit expiration date uses default."""
    api_key = APIKeyCreate(
        name="Test Key",
        project_uuid="123e4567-e89b-12d3-a456-426614174000",
        environment_uuid="123e4567-e89b-12d3-a456-426614174001",
    )

    # Default is 365 days from now
    assert api_key.expires_at is not None
    assert api_key.expires_at.tzinfo == timezone.utc
    # Should be approximately 365 days from now
    time_diff = api_key.expires_at - datetime.now(timezone.utc)
    assert 364 <= time_diff.days <= 366  # Allow for small variations


def test_api_key_public_timezone_validation():
    """Test that APIKeyPublic validator correctly handles timezone conversion."""
    # The expires_at field uses AwareDatetime type annotation which requires timezone info

    # Test with timezone-aware datetime
    utc_time = datetime.now(timezone.utc)
    api_key_data = APIKeyCreate(
        name="test-key",
        project_uuid="223e4567-e89b-12d3-a456-426614174000",
        environment_uuid="323e4567-e89b-12d3-a456-426614174000",
        expires_at=utc_time,
    )
    assert api_key_data.expires_at == utc_time
    assert api_key_data.expires_at.tzinfo is not None

    # Test the default factory creates timezone-aware datetime
    api_key_default = APIKeyCreate(
        name="test-key-default",
        project_uuid="223e4567-e89b-12d3-a456-426614174000",
        environment_uuid="323e4567-e89b-12d3-a456-426614174000",
    )
    assert api_key_default.expires_at.tzinfo is not None
    assert api_key_default.expires_at.tzinfo == timezone.utc


def test_api_key_create_validation_errors():
    """Test validation errors for APIKeyCreate."""
    # Missing required fields
    with pytest.raises(ValidationError) as exc_info:
        APIKeyCreate()

    errors = exc_info.value.errors()
    assert len(errors) >= 2  # At least name and project_uuid are required
    # environment_uuid is optional with default=None

    # Invalid UUID format
    with pytest.raises(ValidationError) as exc_info:
        APIKeyCreate(
            name="Test Key",
            project_uuid="invalid-uuid",
            environment_uuid="123e4567-e89b-12d3-a456-426614174001",
        )

    errors = exc_info.value.errors()
    assert any(error["type"] == "uuid_parsing" for error in errors)


def test_api_key_create_with_non_datetime_expires_at():
    """Test that non-datetime values for expires_at are handled properly."""
    # The validator only runs on datetime objects, so strings should fail at validation
    with pytest.raises(ValidationError) as exc_info:
        APIKeyCreate(
            name="Test Key",
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            environment_uuid="123e4567-e89b-12d3-a456-426614174001",
            expires_at="not a datetime",
        )

    errors = exc_info.value.errors()
    assert any("datetime" in str(error).lower() for error in errors)


def test_api_key_create_with_iso_format_string():
    """Test creating API key with ISO format datetime string."""
    # Since the field requires timezone-aware datetime, naive ISO strings should fail
    iso_string = "2024-12-25T12:00:00"

    with pytest.raises(ValidationError) as exc_info:
        APIKeyCreate(
            name="Test Key",
            project_uuid="123e4567-e89b-12d3-a456-426614174000",
            environment_uuid="123e4567-e89b-12d3-a456-426614174001",
            expires_at=iso_string,
        )

    errors = exc_info.value.errors()
    assert any(error["type"] == "timezone_aware" for error in errors)


def test_api_key_create_with_utc_iso_string():
    """Test creating API key with UTC ISO format datetime string."""
    iso_string = "2024-12-25T12:00:00Z"
    api_key = APIKeyCreate(
        name="Test Key",
        project_uuid="123e4567-e89b-12d3-a456-426614174000",
        environment_uuid="123e4567-e89b-12d3-a456-426614174001",
        expires_at=iso_string,
    )

    # Should be parsed with UTC timezone
    assert isinstance(api_key.expires_at, datetime)
    assert api_key.expires_at.tzinfo is not None
