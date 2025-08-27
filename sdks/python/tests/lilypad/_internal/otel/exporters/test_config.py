"""Unit tests for configuration module."""

from unittest.mock import MagicMock, patch

from lilypad._internal.otel.exporters.config import (
    ConfigureExportersConfig,
    configure_exporters,
)
from lilypad._internal.otel.exporters.processors import LLMSpanProcessor


def test_config_init_with_all_params():
    """Test configuration initialization with all parameters."""
    mock_client = MagicMock()
    config = ConfigureExportersConfig(
        client=mock_client,
        base_url="https://api.lilypad.com",
        timeout=60.0,
        max_retry_attempts=5,
    )
    assert config.client == mock_client
    assert config.base_url == "https://api.lilypad.com"
    assert config.timeout == 60.0
    assert config.max_retry_attempts == 5


def test_config_init_with_defaults():
    """Test configuration initialization with default values."""
    mock_client = MagicMock()
    config = ConfigureExportersConfig(client=mock_client)
    assert config.client == mock_client
    assert config.base_url == "https://api.lilypad.io"
    assert config.timeout == 30.0
    assert config.max_retry_attempts == 3


def test_configure_exporters_creates_processor():
    """Test that configure_exporters creates LLMSpanProcessor."""
    mock_client = MagicMock()
    config = ConfigureExportersConfig(
        client=mock_client,
        base_url="https://api.lilypad.com",
        timeout=45.0,
        max_retry_attempts=5,
    )

    processor = configure_exporters(config)

    assert isinstance(processor, LLMSpanProcessor)
    assert processor.start_exporter is not None
    assert processor.batch_processor is not None
    assert processor.executor is not None


def test_configure_exporters_uses_config_values():
    """Test that configure_exporters uses provided config values."""
    mock_client = MagicMock()
    config = ConfigureExportersConfig(
        client=mock_client,
        base_url="https://api.lilypad.com",
        timeout=45.0,
        max_retry_attempts=10,
    )

    with (
        patch(
            "lilypad._internal.otel.exporters.transport.TelemetryTransport"
        ) as mock_transport_cls,
        patch(
            "lilypad._internal.otel.exporters.transport.TelemetryConfig"
        ) as mock_config_cls,
        patch(
            "lilypad._internal.otel.exporters.exporters.ImmediateStartExporter"
        ) as mock_start_cls,
        patch(
            "lilypad._internal.otel.exporters.exporters.LilypadOTLPExporter"
        ) as mock_otlp_cls,
    ):
        processor = configure_exporters(config)

        mock_config_cls.assert_called_once_with(
            timeout=45.0,
            max_retry_attempts=10,
        )

        mock_transport_cls.assert_called_once()
        transport_call = mock_transport_cls.call_args
        assert transport_call.kwargs["client"] == mock_client

        mock_start_cls.assert_called_once()
        start_call = mock_start_cls.call_args
        assert start_call.kwargs["max_retry_attempts"] == 10

        mock_otlp_cls.assert_called_once()
        otlp_call = mock_otlp_cls.call_args
        assert otlp_call.kwargs["timeout"] == 45.0


def test_configure_exporters_batch_processor_settings():
    """Test that configure_exporters sets correct BatchSpanProcessor settings."""
    mock_client = MagicMock()
    config = ConfigureExportersConfig(client=mock_client)

    with patch("opentelemetry.sdk.trace.export.BatchSpanProcessor") as mock_batch_cls:
        processor = configure_exporters(config)

        mock_batch_cls.assert_called_once()
        batch_call = mock_batch_cls.call_args
        assert batch_call.kwargs["max_queue_size"] == 2048
        assert batch_call.kwargs["schedule_delay_millis"] == 5000
        assert batch_call.kwargs["export_timeout_millis"] == 30000
        assert batch_call.kwargs["max_export_batch_size"] == 512


def test_configure_exporters_executor_settings():
    """Test that configure_exporters sets correct ThreadPoolExecutor settings."""
    mock_client = MagicMock()
    config = ConfigureExportersConfig(client=mock_client)

    with patch("concurrent.futures.ThreadPoolExecutor") as mock_executor_cls:
        processor = configure_exporters(config)

        mock_executor_cls.assert_called_once_with(
            max_workers=2,
            thread_name_prefix="llm-span-processor",
        )
