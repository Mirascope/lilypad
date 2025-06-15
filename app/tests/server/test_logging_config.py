"""Tests for the logging configuration module."""

import logging
import os
import sys
from unittest.mock import Mock, patch

from lilypad.server.logging_config import setup_logging


class TestSetupLogging:
    """Test setup_logging function."""

    @patch("logging.basicConfig")
    @patch("logging.getLogger")
    def test_setup_logging_default_level(self, mock_get_logger, mock_basic_config):
        """Test setup_logging with default INFO level."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        with patch.dict(os.environ, {}, clear=True):
            setup_logging()

        # Check basicConfig was called with correct parameters
        mock_basic_config.assert_called_once_with(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stdout,
            force=True,
        )

    @patch("logging.basicConfig")
    @patch("logging.getLogger")
    def test_setup_logging_debug_level(self, mock_get_logger, mock_basic_config):
        """Test setup_logging with DEBUG level from environment."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            setup_logging()

        mock_basic_config.assert_called_once_with(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stdout,
            force=True,
        )

    @patch("logging.basicConfig")
    @patch("logging.getLogger")
    def test_setup_logging_warning_level(self, mock_get_logger, mock_basic_config):
        """Test setup_logging with WARNING level from environment."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        with patch.dict(os.environ, {"LOG_LEVEL": "WARNING"}):
            setup_logging()

        mock_basic_config.assert_called_once_with(
            level=logging.WARNING,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stdout,
            force=True,
        )

    @patch("logging.basicConfig")
    @patch("logging.getLogger")
    def test_setup_logging_error_level(self, mock_get_logger, mock_basic_config):
        """Test setup_logging with ERROR level from environment."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        with patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}):
            setup_logging()

        mock_basic_config.assert_called_once_with(
            level=logging.ERROR,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stdout,
            force=True,
        )

    @patch("logging.basicConfig")
    @patch("logging.getLogger")
    def test_setup_logging_critical_level(self, mock_get_logger, mock_basic_config):
        """Test setup_logging with CRITICAL level from environment."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        with patch.dict(os.environ, {"LOG_LEVEL": "CRITICAL"}):
            setup_logging()

        mock_basic_config.assert_called_once_with(
            level=logging.CRITICAL,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stdout,
            force=True,
        )

    @patch("logging.basicConfig")
    @patch("logging.getLogger")
    def test_setup_logging_lowercase_level(self, mock_get_logger, mock_basic_config):
        """Test setup_logging with lowercase level (should be converted to uppercase)."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        with patch.dict(os.environ, {"LOG_LEVEL": "debug"}):
            setup_logging()

        mock_basic_config.assert_called_once_with(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stdout,
            force=True,
        )

    @patch("logging.basicConfig")
    @patch("logging.getLogger")
    def test_setup_logging_invalid_level(self, mock_get_logger, mock_basic_config):
        """Test setup_logging with invalid level defaults to INFO."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID_LEVEL"}):
            setup_logging()

        # Should fall back to INFO level
        mock_basic_config.assert_called_once_with(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stdout,
            force=True,
        )

    @patch("logging.basicConfig")
    @patch("logging.getLogger")
    def test_setup_logging_configures_specific_loggers(
        self, mock_get_logger, mock_basic_config
    ):
        """Test setup_logging configures specific lilypad loggers."""
        mock_loggers = {}

        def mock_get_logger_side_effect(name):
            if name not in mock_loggers:
                mock_loggers[name] = Mock()
            return mock_loggers[name]

        mock_get_logger.side_effect = mock_get_logger_side_effect

        with patch.dict(os.environ, {}, clear=True):
            setup_logging()

        # Check that specific loggers were configured
        expected_loggers = [
            "lilypad",
            "lilypad.server.services.kafka",
            "lilypad.server.services.kafka_setup",
            "lilypad.server.services.span_queue_processor",
            "lilypad.server.api.v0.traces_api",
        ]

        for logger_name in expected_loggers:
            assert logger_name in mock_loggers
            mock_loggers[logger_name].setLevel.assert_called_with(logging.INFO)

    @patch("logging.basicConfig")
    @patch("logging.getLogger")
    def test_setup_logging_reduces_noise_loggers(
        self, mock_get_logger, mock_basic_config
    ):
        """Test setup_logging reduces noise from uvicorn and httpx loggers."""
        mock_loggers = {}

        def mock_get_logger_side_effect(name):
            if name not in mock_loggers:
                mock_loggers[name] = Mock()
            return mock_loggers[name]

        mock_get_logger.side_effect = mock_get_logger_side_effect

        with patch.dict(os.environ, {}, clear=True):
            setup_logging()

        # Check that noise loggers were set to WARNING
        assert "uvicorn.access" in mock_loggers
        mock_loggers["uvicorn.access"].setLevel.assert_called_with(logging.WARNING)

        assert "httpx" in mock_loggers
        mock_loggers["httpx"].setLevel.assert_called_with(logging.WARNING)

    @patch("logging.basicConfig")
    @patch("logging.getLogger")
    def test_setup_logging_logs_configuration(self, mock_get_logger, mock_basic_config):
        """Test setup_logging logs the configuration information."""
        mock_loggers = {}

        def mock_get_logger_side_effect(name):
            if name not in mock_loggers:
                mock_loggers[name] = Mock()
            return mock_loggers[name]

        mock_get_logger.side_effect = mock_get_logger_side_effect

        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}, clear=True):
            setup_logging()

        # Check that the module logger was used to log configuration
        module_logger_name = "lilypad.server.logging_config"
        assert module_logger_name in mock_loggers

        module_logger = mock_loggers[module_logger_name]
        module_logger.info.assert_any_call("Logging configured with level: DEBUG")
        module_logger.info.assert_any_call("Python unbuffered: Not set")

    @patch("logging.basicConfig")
    @patch("logging.getLogger")
    def test_setup_logging_with_pythonunbuffered(
        self, mock_get_logger, mock_basic_config
    ):
        """Test setup_logging logs PYTHONUNBUFFERED environment variable."""
        mock_loggers = {}

        def mock_get_logger_side_effect(name):
            if name not in mock_loggers:
                mock_loggers[name] = Mock()
            return mock_loggers[name]

        mock_get_logger.side_effect = mock_get_logger_side_effect

        with patch.dict(os.environ, {"PYTHONUNBUFFERED": "1"}, clear=True):
            setup_logging()

        # Check that PYTHONUNBUFFERED was logged
        module_logger_name = "lilypad.server.logging_config"
        assert module_logger_name in mock_loggers

        module_logger = mock_loggers[module_logger_name]
        module_logger.info.assert_any_call("Python unbuffered: 1")

    @patch("logging.basicConfig")
    def test_setup_logging_stream_is_stdout(self, mock_basic_config):
        """Test setup_logging uses sys.stdout as stream."""
        with patch.dict(os.environ, {}, clear=True), patch("logging.getLogger"):
            setup_logging()

        # Verify that sys.stdout was passed as stream
        call_args = mock_basic_config.call_args
        assert call_args[1]["stream"] is sys.stdout

    @patch("logging.basicConfig")
    def test_setup_logging_force_override(self, mock_basic_config):
        """Test setup_logging uses force=True to override existing configuration."""
        with patch.dict(os.environ, {}, clear=True), patch("logging.getLogger"):
            setup_logging()

        # Verify that force=True was passed
        call_args = mock_basic_config.call_args
        assert call_args[1]["force"] is True

    @patch("logging.basicConfig")
    @patch("logging.getLogger")
    def test_setup_logging_format_string(self, mock_get_logger, mock_basic_config):
        """Test setup_logging uses correct format string."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        with patch.dict(os.environ, {}, clear=True):
            setup_logging()

        call_args = mock_basic_config.call_args
        expected_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        assert call_args[1]["format"] == expected_format

    @patch("logging.basicConfig")
    @patch("logging.getLogger")
    def test_setup_logging_date_format(self, mock_get_logger, mock_basic_config):
        """Test setup_logging uses correct date format."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        with patch.dict(os.environ, {}, clear=True):
            setup_logging()

        call_args = mock_basic_config.call_args
        expected_datefmt = "%Y-%m-%d %H:%M:%S"
        assert call_args[1]["datefmt"] == expected_datefmt

    @patch("logging.basicConfig")
    @patch("logging.getLogger")
    def test_setup_logging_getattr_fallback(self, mock_get_logger, mock_basic_config):
        """Test setup_logging getattr fallback for invalid log levels."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Test that invalid log level falls back to INFO
        # This is already tested in test_setup_logging_invalid_level
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID_LEVEL"}):
            setup_logging()

        # Should use the default (logging.INFO) when level is invalid
        call_args = mock_basic_config.call_args
        assert call_args[1]["level"] == logging.INFO

    def test_setup_logging_integration(self):
        """Integration test for setup_logging function."""
        # Save original logging configuration
        original_level = logging.root.level
        original_handlers = logging.root.handlers[:]

        try:
            # Clear existing handlers
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)

            with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
                setup_logging()

            # Verify root logger level was set
            assert logging.root.level == logging.DEBUG

            # Verify lilypad logger is configured
            lilypad_logger = logging.getLogger("lilypad")
            assert lilypad_logger.level == logging.INFO

            # Verify noise reduction
            uvicorn_logger = logging.getLogger("uvicorn.access")
            assert uvicorn_logger.level == logging.WARNING

        finally:
            # Restore original configuration
            logging.root.level = original_level
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)
            for handler in original_handlers:
                logging.root.addHandler(handler)
