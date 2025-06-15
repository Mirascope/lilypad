"""Unit tests for Secret Manager Factory."""

from unittest.mock import Mock, patch

import pytest
from moto import mock_aws
from sqlmodel import Session

from lilypad.server.secret_manager.aws_secret_manager import AWSSecretManager
from lilypad.server.secret_manager.secret_manager_factory import (
    SecretManagerType,
    get_secret_manager,
)
from lilypad.server.secret_manager.supabase_vault_manager import SupabaseVaultManager
from lilypad.server.settings import Settings


def test_get_supabase_vault_manager_with_session():
    """Test getting Supabase Vault Manager with session."""
    mock_session = Mock(spec=Session)

    manager = get_secret_manager(
        session=mock_session, manager_type=SecretManagerType.SUPABASE_VAULT
    )

    assert isinstance(manager, SupabaseVaultManager)


def test_get_supabase_vault_manager_without_session_raises_error():
    """Test getting Supabase Vault Manager without session raises error."""
    with pytest.raises(
        ValueError, match="Session is required for Supabase Vault Manager"
    ):
        get_secret_manager(manager_type=SecretManagerType.SUPABASE_VAULT)


@mock_aws
def test_get_aws_secret_manager():
    """Test getting AWS Secret Manager."""
    manager = get_secret_manager(manager_type=SecretManagerType.AWS_SECRET_MANAGER)

    assert isinstance(manager, AWSSecretManager)


@mock_aws
def test_get_aws_secret_manager_with_custom_region():
    """Test getting AWS Secret Manager with custom region from settings."""
    mock_settings = Mock(spec=Settings)
    mock_settings.aws_region = "eu-west-1"
    mock_settings.aws_secret_manager_force_delete = False
    mock_settings.aws_secret_manager_max_retries = 3
    mock_settings.aws_secret_manager_enable_metrics = True

    with patch(
        "lilypad.server.secret_manager.secret_manager_factory.get_settings",
        return_value=mock_settings,
    ):
        manager = get_secret_manager(manager_type=SecretManagerType.AWS_SECRET_MANAGER)

        assert isinstance(manager, AWSSecretManager)
        assert manager.config.region_name == "eu-west-1"


def test_get_manager_from_settings_supabase():
    """Test getting manager type from settings - Supabase."""
    mock_session = Mock(spec=Session)
    mock_settings = Mock(spec=Settings)
    mock_settings.secret_manager_type = "SUPABASE_VAULT"

    with patch(
        "lilypad.server.secret_manager.secret_manager_factory.get_settings",
        return_value=mock_settings,
    ):
        manager = get_secret_manager(session=mock_session)

        assert isinstance(manager, SupabaseVaultManager)


@mock_aws
def test_get_manager_from_settings_aws():
    """Test getting manager type from settings - AWS."""
    mock_settings = Mock(spec=Settings)
    mock_settings.secret_manager_type = "AWS_SECRET_MANAGER"
    mock_settings.aws_region = "us-east-1"
    mock_settings.aws_secret_manager_force_delete = False
    mock_settings.aws_secret_manager_max_retries = 3
    mock_settings.aws_secret_manager_enable_metrics = True

    with patch(
        "lilypad.server.secret_manager.secret_manager_factory.get_settings",
        return_value=mock_settings,
    ):
        manager = get_secret_manager()

        assert isinstance(manager, AWSSecretManager)


def test_get_manager_with_invalid_settings_type():
    """Test getting manager with invalid settings type raises error."""
    mock_settings = Mock(spec=Settings)
    mock_settings.secret_manager_type = "INVALID_TYPE"

    with (
        patch(
            "lilypad.server.secret_manager.secret_manager_factory.get_settings",
            return_value=mock_settings,
        ),
        pytest.raises(ValueError, match="Invalid SECRET_MANAGER_TYPE"),
    ):
        get_secret_manager()


def test_get_manager_with_unsupported_enum_type():
    """Test getting manager with unsupported SecretManagerType enum value."""
    from unittest.mock import Mock
    
    # Create a mock enum value that's not in the if/elif chain
    mock_unsupported_type = Mock()
    mock_unsupported_type.__str__ = Mock(return_value="UNSUPPORTED_TYPE")
    
    with pytest.raises(ValueError, match="Unsupported secret manager type"):
        get_secret_manager(manager_type=mock_unsupported_type)


def test_default_manager_type_is_supabase():
    """Test that default manager type is Supabase Vault when not set."""
    mock_session = Mock(spec=Session)
    mock_settings = Mock(spec=Settings)
    mock_settings.secret_manager_type = "SUPABASE_VAULT"  # Default value

    with patch(
        "lilypad.server.secret_manager.secret_manager_factory.get_settings",
        return_value=mock_settings,
    ):
        manager = get_secret_manager(session=mock_session)

        assert isinstance(manager, SupabaseVaultManager)


@mock_aws
def test_aws_manager_uses_default_region_when_not_set():
    """Test AWS manager uses default region from settings."""
    mock_settings = Mock(spec=Settings)
    mock_settings.aws_region = "us-east-1"  # Default value
    mock_settings.aws_secret_manager_force_delete = False
    mock_settings.aws_secret_manager_max_retries = 3
    mock_settings.aws_secret_manager_enable_metrics = True

    with patch(
        "lilypad.server.secret_manager.secret_manager_factory.get_settings",
        return_value=mock_settings,
    ):
        manager = get_secret_manager(manager_type=SecretManagerType.AWS_SECRET_MANAGER)

        assert isinstance(manager, AWSSecretManager)
        assert manager.config.region_name == "us-east-1"  # Default region


def test_explicit_manager_type_overrides_settings():
    """Test that explicit manager_type parameter overrides settings."""
    mock_session = Mock(spec=Session)
    mock_settings = Mock(spec=Settings)
    mock_settings.secret_manager_type = "AWS_SECRET_MANAGER"  # Settings says AWS
    mock_settings.aws_region = "us-east-1"
    mock_settings.aws_secret_manager_force_delete = False
    mock_settings.aws_secret_manager_max_retries = 3
    mock_settings.aws_secret_manager_enable_metrics = True

    with patch(
        "lilypad.server.secret_manager.secret_manager_factory.get_settings",
        return_value=mock_settings,
    ):
        # But we explicitly request Supabase
        manager = get_secret_manager(
            session=mock_session, manager_type=SecretManagerType.SUPABASE_VAULT
        )

        assert isinstance(manager, SupabaseVaultManager)


@mock_aws
def test_factory_with_all_parameters():
    """Test factory with all parameters provided."""
    mock_session = Mock(spec=Session)
    mock_settings = Mock(spec=Settings)
    mock_settings.aws_region = "ap-southeast-1"
    mock_settings.aws_secret_manager_force_delete = True
    mock_settings.aws_secret_manager_max_retries = 5
    mock_settings.aws_secret_manager_enable_metrics = True

    with patch(
        "lilypad.server.secret_manager.secret_manager_factory.get_settings",
        return_value=mock_settings,
    ):
        # Test AWS with region
        aws_manager = get_secret_manager(
            session=mock_session,  # Will be ignored for AWS
            manager_type=SecretManagerType.AWS_SECRET_MANAGER,
        )
        assert isinstance(aws_manager, AWSSecretManager)
        assert aws_manager.config.region_name == "ap-southeast-1"
        assert aws_manager.config.force_delete is True
        assert aws_manager.config.max_retries == 5

        # Test Supabase with session
        supabase_manager = get_secret_manager(
            session=mock_session, manager_type=SecretManagerType.SUPABASE_VAULT
        )
        assert isinstance(supabase_manager, SupabaseVaultManager)
