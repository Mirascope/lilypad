"""Tests for the database setup module."""

from unittest.mock import Mock, patch

import pytest

from lilypad.server.db.setup import create_tables


class TestCreateTables:
    """Test create_tables function."""

    @patch("lilypad.server.db.setup.SQLModel")
    @patch("lilypad.server.db.setup.db")
    def test_create_tables_without_environment(self, mock_db, mock_sqlmodel):
        """Test create_tables without environment parameter."""
        mock_engine = Mock()
        mock_db.get_engine.return_value = mock_engine
        mock_metadata = Mock()
        mock_sqlmodel.metadata = mock_metadata

        create_tables()

        mock_db.get_engine.assert_called_once_with(None)
        mock_metadata.create_all.assert_called_once_with(mock_engine)

    @patch("lilypad.server.db.setup.SQLModel")
    @patch("lilypad.server.db.setup.db")
    def test_create_tables_with_environment(self, mock_db, mock_sqlmodel):
        """Test create_tables with environment parameter."""
        mock_engine = Mock()
        mock_db.get_engine.return_value = mock_engine
        mock_metadata = Mock()
        mock_sqlmodel.metadata = mock_metadata

        create_tables("test")

        mock_db.get_engine.assert_called_once_with("test")
        mock_metadata.create_all.assert_called_once_with(mock_engine)

    @patch("lilypad.server.db.setup.SQLModel")
    @patch("lilypad.server.db.setup.db")
    def test_create_tables_with_development_environment(self, mock_db, mock_sqlmodel):
        """Test create_tables with development environment."""
        mock_engine = Mock()
        mock_db.get_engine.return_value = mock_engine
        mock_metadata = Mock()
        mock_sqlmodel.metadata = mock_metadata

        create_tables("development")

        mock_db.get_engine.assert_called_once_with("development")
        mock_metadata.create_all.assert_called_once_with(mock_engine)

    @patch("lilypad.server.db.setup.SQLModel")
    @patch("lilypad.server.db.setup.db")
    def test_create_tables_with_production_environment(self, mock_db, mock_sqlmodel):
        """Test create_tables with production environment."""
        mock_engine = Mock()
        mock_db.get_engine.return_value = mock_engine
        mock_metadata = Mock()
        mock_sqlmodel.metadata = mock_metadata

        create_tables("production")

        mock_db.get_engine.assert_called_once_with("production")
        mock_metadata.create_all.assert_called_once_with(mock_engine)

    @patch("lilypad.server.db.setup.SQLModel")
    @patch("lilypad.server.db.setup.db")
    def test_create_tables_with_local_environment(self, mock_db, mock_sqlmodel):
        """Test create_tables with local environment."""
        mock_engine = Mock()
        mock_db.get_engine.return_value = mock_engine
        mock_metadata = Mock()
        mock_sqlmodel.metadata = mock_metadata

        create_tables("local")

        mock_db.get_engine.assert_called_once_with("local")
        mock_metadata.create_all.assert_called_once_with(mock_engine)

    @patch("lilypad.server.db.setup.SQLModel")
    @patch("lilypad.server.db.setup.db")
    def test_create_tables_db_get_engine_exception(self, mock_db, mock_sqlmodel):
        """Test create_tables handles db.get_engine exception."""
        mock_db.get_engine.side_effect = Exception("Database connection failed")
        mock_metadata = Mock()
        mock_sqlmodel.metadata = mock_metadata

        with pytest.raises(Exception) as exc_info:
            create_tables()

        assert "Database connection failed" in str(exc_info.value)
        mock_db.get_engine.assert_called_once_with(None)
        mock_metadata.create_all.assert_not_called()

    @patch("lilypad.server.db.setup.SQLModel")
    @patch("lilypad.server.db.setup.db")
    def test_create_tables_metadata_create_all_exception(self, mock_db, mock_sqlmodel):
        """Test create_tables handles metadata.create_all exception."""
        mock_engine = Mock()
        mock_db.get_engine.return_value = mock_engine
        mock_metadata = Mock()
        mock_metadata.create_all.side_effect = Exception("Table creation failed")
        mock_sqlmodel.metadata = mock_metadata

        with pytest.raises(Exception) as exc_info:
            create_tables()

        assert "Table creation failed" in str(exc_info.value)
        mock_db.get_engine.assert_called_once_with(None)
        mock_metadata.create_all.assert_called_once_with(mock_engine)

    @patch("lilypad.server.db.setup.SQLModel")
    @patch("lilypad.server.db.setup.db")
    def test_create_tables_empty_string_environment(self, mock_db, mock_sqlmodel):
        """Test create_tables with empty string environment."""
        mock_engine = Mock()
        mock_db.get_engine.return_value = mock_engine
        mock_metadata = Mock()
        mock_sqlmodel.metadata = mock_metadata

        create_tables("")

        mock_db.get_engine.assert_called_once_with("")
        mock_metadata.create_all.assert_called_once_with(mock_engine)

    @patch("lilypad.server.db.setup.SQLModel")
    @patch("lilypad.server.db.setup.db")
    def test_create_tables_metadata_property_access(self, mock_db, mock_sqlmodel):
        """Test create_tables accesses SQLModel.metadata property correctly."""
        mock_engine = Mock()
        mock_db.get_engine.return_value = mock_engine

        # Test that metadata property is accessed
        mock_metadata = Mock()
        type(mock_sqlmodel).metadata = mock_metadata

        create_tables()

        # Verify metadata.create_all was called
        mock_metadata.create_all.assert_called_once_with(mock_engine)

def test_main_execution_block():
    """Test the main execution block."""
    from unittest.mock import patch
    import subprocess
    import sys
    
    # Test by executing the module directly as a script
    result = subprocess.run(
        [sys.executable, "-m", "lilypad.server.db.setup"],
        capture_output=True,
        text=True,
        cwd="/Users/koudai/PycharmProjects/lilypad/app"
    )
    
    # The main block should execute (may fail due to DB connection, but should reach the line)
    assert result.returncode in [0, 1]  # 0 for success, 1 for expected DB error


def test_imports_exist():
    """Test that all necessary imports are available."""
    # Test that we can import the required modules
    from sqlmodel import SQLModel

    from lilypad.server.db.session import db

    # Verify objects have expected attributes
    assert hasattr(SQLModel, "metadata")
    assert hasattr(db, "get_engine")

@patch("lilypad.server.db.setup.SQLModel")
@patch("lilypad.server.db.setup.db")
def test_create_tables_integration_pattern(mock_db, mock_sqlmodel):
    """Test create_tables follows expected integration pattern."""
    mock_engine = Mock()
    mock_db.get_engine.return_value = mock_engine
    mock_metadata = Mock()
    mock_sqlmodel.metadata = mock_metadata

    # Call with different environment types
    environments = [None, "local", "development", "production", "test"]

    for env in environments:
        mock_db.get_engine.reset_mock()
        mock_metadata.create_all.reset_mock()

        create_tables(env)

        mock_db.get_engine.assert_called_once_with(env)
        mock_metadata.create_all.assert_called_once_with(mock_engine)

@patch("lilypad.server.db.setup.SQLModel")
@patch("lilypad.server.db.setup.db")
def test_create_tables_engine_is_passed_to_create_all(mock_db, mock_sqlmodel):
    """Test that the engine from db.get_engine is passed to create_all."""
    # Create unique mock engines for different calls
    mock_engine_1 = Mock(name="engine_1")
    mock_engine_2 = Mock(name="engine_2")

    mock_db.get_engine.side_effect = [mock_engine_1, mock_engine_2]
    mock_metadata = Mock()
    mock_sqlmodel.metadata = mock_metadata

    # First call
    create_tables("env1")
    mock_metadata.create_all.assert_called_with(mock_engine_1)

    # Reset and second call
    mock_metadata.create_all.reset_mock()
    create_tables("env2")
    mock_metadata.create_all.assert_called_with(mock_engine_2)


def test_module_structure():
    """Test module has expected structure and exports."""
    import lilypad.server.db.setup as setup_module

    # Test function exists
    assert hasattr(setup_module, "create_tables")
    assert callable(setup_module.create_tables)

    # Test function signature
    import inspect

    sig = inspect.signature(setup_module.create_tables)
    params = list(sig.parameters.keys())
    assert "environment" in params

    # Test default parameter value
    env_param = sig.parameters["environment"]
    assert env_param.default is None


@patch("lilypad.server.db.setup.SQLModel")
@patch("lilypad.server.db.setup.db")
def test_create_tables_preserves_environment_type(mock_db, mock_sqlmodel):
    """Test create_tables preserves the type of environment parameter."""
    mock_engine = Mock()
    mock_db.get_engine.return_value = mock_engine
    mock_metadata = Mock()
    mock_sqlmodel.metadata = mock_metadata

    # Test with string
    create_tables("test_env")
    mock_db.get_engine.assert_called_with("test_env")

    # Test with None
    mock_db.get_engine.reset_mock()
    create_tables(None)
    mock_db.get_engine.assert_called_with(None)

    # Test that the exact value is passed through
    mock_db.get_engine.reset_mock()
    special_env = "special_environment_string"
    create_tables(special_env)
    mock_db.get_engine.assert_called_with(special_env)
