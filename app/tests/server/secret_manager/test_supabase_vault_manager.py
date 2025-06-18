"""Unit tests for Supabase Vault Manager implementation."""

import contextlib
from unittest.mock import Mock

import pytest
from sqlmodel import Session

from lilypad.server.secret_manager.supabase_vault_manager import SupabaseVaultManager


@pytest.fixture
def mock_session():
    """Create a mock SQLModel session."""
    return Mock(spec=Session)


@pytest.fixture
def vault_manager(mock_session):
    """Create a SupabaseVaultManager instance for testing."""
    return SupabaseVaultManager(mock_session)


def test_init(mock_session):
    """Test SupabaseVaultManager initialization."""
    manager = SupabaseVaultManager(mock_session)
    assert manager.session is mock_session


def test_store_secret_success(vault_manager, mock_session):
    """Test successful secret storage."""
    # Mock execute result
    mock_result = Mock()
    mock_result.scalar_one.return_value = "secret-id-123"
    mock_session.execute.return_value = mock_result

    # Store secret
    secret_id = vault_manager.store_secret(
        name="test_secret",
        secret="my-secret-value",
        description="Test secret description",
    )

    # Verify result
    assert secret_id == "secret-id-123"

    # Verify session calls
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


def test_store_secret_without_description(vault_manager, mock_session):
    """Test storing secret without description."""
    mock_result = Mock()
    mock_result.scalar_one.return_value = "secret-id-456"
    mock_session.execute.return_value = mock_result

    secret_id = vault_manager.store_secret(
        name="test_secret_no_desc", secret="my-secret-value"
    )

    assert secret_id == "secret-id-456"
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


def test_store_secret_transaction_rollback(vault_manager, mock_session):
    """Test transaction rollback on store secret error."""
    # Mock execute to raise exception
    mock_session.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        vault_manager.store_secret("test", "secret", "description")

    # Verify rollback was called
    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()


def test_get_secret_success(vault_manager, mock_session):
    """Test successful secret retrieval."""
    # Mock execute result
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = "decrypted-secret-value"
    mock_session.execute.return_value = mock_result

    # Get secret
    secret = vault_manager.get_secret("secret-id-123")

    # Verify result
    assert secret == "decrypted-secret-value"

    # Verify session calls
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


def test_get_secret_not_found(vault_manager, mock_session):
    """Test getting non-existent secret."""
    # Mock execute result for not found
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Get secret
    secret = vault_manager.get_secret("non-existent-id")

    # Verify result
    assert secret is None
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


def test_get_secret_transaction_rollback(vault_manager, mock_session):
    """Test transaction rollback on get secret error."""
    mock_session.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        vault_manager.get_secret("secret-id")

    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()


def test_update_secret_success(vault_manager, mock_session):
    """Test successful secret update."""
    # Update secret
    result = vault_manager.update_secret("secret-id-123", "new-secret-value")

    # Verify result
    assert result is True

    # Verify session calls
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


def test_update_secret_transaction_rollback(vault_manager, mock_session):
    """Test transaction rollback on update secret error."""
    mock_session.execute.side_effect = Exception("Update failed")

    with pytest.raises(Exception, match="Update failed"):
        vault_manager.update_secret("secret-id", "new-value")

    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()


def test_delete_secret_success(vault_manager, mock_session):
    """Test successful secret deletion."""
    # Mock execute result for successful deletion
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = "secret-id-123"
    mock_session.execute.return_value = mock_result

    # Delete secret
    result = vault_manager.delete_secret("secret-id-123")

    # Verify result
    assert result is True

    # Verify session calls
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


def test_delete_secret_not_found(vault_manager, mock_session):
    """Test deleting non-existent secret."""
    # Mock execute result for not found
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Delete secret
    result = vault_manager.delete_secret("non-existent-id")

    # Verify result
    assert result is False
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


def test_delete_secret_transaction_rollback(vault_manager, mock_session):
    """Test transaction rollback on delete secret error."""
    mock_session.execute.side_effect = Exception("Delete failed")

    with pytest.raises(Exception, match="Delete failed"):
        vault_manager.delete_secret("secret-id")

    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()


def test_get_secret_id_by_name_success(vault_manager, mock_session):
    """Test successful secret ID retrieval by name."""
    # Mock execute result
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = "secret-id-789"
    mock_session.execute.return_value = mock_result

    # Get secret ID
    secret_id = vault_manager.get_secret_id_by_name("test_secret")

    # Verify result
    assert secret_id == "secret-id-789"
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


def test_get_secret_id_by_name_not_found(vault_manager, mock_session):
    """Test getting secret ID for non-existent name."""
    # Mock execute result for not found
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Get secret ID
    secret_id = vault_manager.get_secret_id_by_name("non_existent_secret")

    # Verify result
    assert secret_id is None
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


def test_get_secret_id_by_name_transaction_rollback(vault_manager, mock_session):
    """Test transaction rollback on get secret ID by name error."""
    mock_session.execute.side_effect = Exception("Query failed")

    with pytest.raises(Exception, match="Query failed"):
        vault_manager.get_secret_id_by_name("test_secret")

    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()


def test_get_secret_name_by_id_success(vault_manager, mock_session):
    """Test successful secret name retrieval by ID."""
    # Mock execute result
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = "test_secret_name"
    mock_session.execute.return_value = mock_result

    # Get secret name
    secret_name = vault_manager.get_secret_name_by_id("secret-id-123")

    # Verify result
    assert secret_name == "test_secret_name"
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


def test_get_secret_name_by_id_not_found(vault_manager, mock_session):
    """Test getting secret name for non-existent ID."""
    # Mock execute result for not found
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Get secret name
    secret_name = vault_manager.get_secret_name_by_id("non-existent-id")

    # Verify result
    assert secret_name is None
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


def test_get_secret_name_by_id_transaction_rollback(vault_manager, mock_session):
    """Test transaction rollback on get secret name by ID error."""
    mock_session.execute.side_effect = Exception("Query failed")

    with pytest.raises(Exception, match="Query failed"):
        vault_manager.get_secret_name_by_id("secret-id")

    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()


def test_transaction_context_manager_success(vault_manager, mock_session):
    """Test transaction context manager with successful operation."""
    with vault_manager._transaction() as session:
        assert session is mock_session
        # Simulate some operation
        session.execute("SELECT 1")

    # Verify commit was called
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()


def test_transaction_context_manager_exception(vault_manager, mock_session):
    """Test transaction context manager with exception."""
    # Need to keep nested to test proper flow
    with pytest.raises(ValueError, match="Test error"):  # noqa: SIM117
        with vault_manager._transaction() as session:
            assert session is mock_session
            raise ValueError("Test error")

    # Verify rollback was called
    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()


def test_transaction_context_manager_nested_exception(vault_manager, mock_session):
    """Test transaction context manager handles nested exceptions."""
    # Make rollback also raise an exception
    mock_session.rollback.side_effect = Exception("Rollback failed")

    # Need to keep nested to test rollback exception behavior
    with pytest.raises(Exception, match="Rollback failed"):  # noqa: SIM117
        with vault_manager._transaction():
            raise ValueError("Test error")

    # Verify rollback was attempted
    mock_session.rollback.assert_called_once()


def test_all_methods_use_transaction_context(vault_manager, mock_session):
    """Test that all methods properly use the transaction context."""
    methods_to_test = [
        ("store_secret", ("name", "secret"), {}),
        ("get_secret", ("secret-id",), {}),
        ("update_secret", ("secret-id", "new-secret"), {}),
        ("delete_secret", ("secret-id",), {}),
        ("get_secret_id_by_name", ("name",), {}),
        ("get_secret_name_by_id", ("secret-id",), {}),
    ]

    for method_name, args, kwargs in methods_to_test:
        # Reset mocks
        mock_session.reset_mock()

        # Mock successful execution
        mock_result = Mock()
        mock_result.scalar_one.return_value = "result"
        mock_result.scalar_one_or_none.return_value = "result"
        mock_session.execute.return_value = mock_result

        # Call method
        method = getattr(vault_manager, method_name)
        with contextlib.suppress(Exception):
            method(*args, **kwargs)
            # Some methods might fail due to incomplete mocking, but that's ok
            # We just want to verify transaction usage

        # Verify commit or rollback was called (depending on whether exception occurred)
        assert mock_session.commit.called or mock_session.rollback.called
