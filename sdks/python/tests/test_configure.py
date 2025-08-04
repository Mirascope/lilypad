"""Comprehensive tests for the Lilypad configuration module."""

import logging
import os
from unittest.mock import Mock, patch
import pytest
import httpx
from opentelemetry import trace
from opentelemetry.trace import INVALID_SPAN_ID, INVALID_TRACE_ID

from lilypad._configure import (
    CryptoIdGenerator,
    _JSONSpanExporter,
    configure,
    lilypad_config,
)
from lilypad.exceptions import LilypadException
from lilypad._utils.settings import Settings


def test_generate_span_id():
    """Test that span IDs are generated correctly."""
    generator = CryptoIdGenerator()

    # Generate multiple span IDs
    span_ids = [generator.generate_span_id() for _ in range(100)]

    # Check all are unique
    assert len(set(span_ids)) == 100

    # Check all are valid (not INVALID_SPAN_ID)
    assert all(sid != INVALID_SPAN_ID for sid in span_ids)

    # Check all are within 64-bit range
    assert all(0 < sid < 2**64 for sid in span_ids)


def test_generate_trace_id():
    """Test that trace IDs are generated correctly."""
    generator = CryptoIdGenerator()

    # Generate multiple trace IDs
    trace_ids = [generator.generate_trace_id() for _ in range(100)]

    # Check all are unique
    assert len(set(trace_ids)) == 100

    # Check all are valid (not INVALID_TRACE_ID)
    assert all(tid != INVALID_TRACE_ID for tid in trace_ids)

    # Check all are within 128-bit range
    assert all(0 < tid < 2**128 for tid in trace_ids)


@patch("lilypad._configure.token_bytes")
def test_regenerate_invalid_ids(mock_token_bytes):
    """Test that invalid IDs are regenerated."""
    generator = CryptoIdGenerator()

    # Mock to return invalid ID first, then valid
    mock_token_bytes.side_effect = [
        b"\x00" * 8,  # Invalid span ID (0)
        b"\x00" * 8 + b"\x01",  # Valid span ID
    ]

    span_id = generator.generate_span_id()
    assert span_id != INVALID_SPAN_ID
    assert mock_token_bytes.call_count == 2


@patch("lilypad._configure.get_sync_client")
@patch("lilypad._configure.get_settings")
def test_init(mock_get_settings, mock_get_client):
    """Test exporter initialization."""
    mock_settings = Mock(api_key="test-key", project_id="test-project", timeout=10.0)
    mock_get_settings.return_value = mock_settings

    exporter = _JSONSpanExporter()

    assert exporter.settings == mock_settings
    mock_get_client.assert_called_once_with(api_key="test-key", timeout=10.0)
    assert isinstance(exporter._logged_trace_ids, set)


@patch("lilypad._configure.get_sync_client")
@patch("lilypad._configure.get_settings")
def test_export_empty_spans(mock_get_settings, mock_get_client):
    """Test exporting empty span list."""
    mock_get_settings.return_value = Mock(api_key="test-key", timeout=10.0)
    exporter = _JSONSpanExporter()

    result = exporter.export([])
    assert result.name == "SUCCESS"


@patch("lilypad._configure.get_sync_client")
@patch("lilypad._configure.get_settings")
def test_export_success(mock_get_settings, mock_get_client):
    """Test successful span export."""
    mock_settings = Mock(
        api_key="test-key", project_id="test-project", remote_client_url="https://app.lilypad.com", timeout=10.0
    )
    mock_get_settings.return_value = mock_settings

    # Mock client response
    mock_response = Mock(trace_status="queued", span_count=2, trace_ids=["trace-1", "trace-2"])
    mock_client = Mock()
    mock_client.projects.traces.create.return_value = mock_response
    mock_get_client.return_value = mock_client

    # Create mock spans
    mock_span = Mock()
    mock_span.context = Mock(trace_id=123456789, span_id=987654321)
    mock_span.parent = None
    mock_span.instrumentation_scope = Mock(
        name="test-scope", version="1.0.0", schema_url="test-url", attributes=Mock(items=lambda: [("key", "value")])
    )
    mock_span.resource = Mock()
    mock_span.resource.to_json.return_value = {"resource": "data"}
    mock_span.name = "test-span"
    mock_span.start_time = 1000
    mock_span.end_time = 2000
    mock_span.attributes = Mock(items=lambda: [("attr1", "value1")], get=lambda k: None)
    mock_status_code = Mock()
    mock_status_code.name = "OK"
    mock_span.status = Mock(status_code=mock_status_code)
    mock_span.events = []
    mock_span.links = []

    exporter = _JSONSpanExporter()
    result = exporter.export([mock_span])

    assert result.name == "SUCCESS"
    mock_client.projects.traces.create.assert_called_once()


@patch("lilypad._configure.get_sync_client")
@patch("lilypad._configure.get_settings")
def test_export_failure(mock_get_settings, mock_get_client):
    """Test span export failure."""
    mock_get_settings.return_value = Mock(api_key="test-key", project_id="test-project", timeout=3.0)

    # Mock client to raise exception
    mock_client = Mock()
    mock_client.projects.traces.create.side_effect = LilypadException("Server error")
    mock_get_client.return_value = mock_client

    # Create minimal mock span
    mock_span = Mock()
    mock_span.context = Mock(trace_id=123, span_id=456)
    mock_span.parent = None
    mock_span.instrumentation_scope = None
    mock_span.resource = Mock()
    mock_span.resource.to_json.return_value = {}
    mock_span.name = "test"
    mock_span.start_time = 1000
    mock_span.end_time = 2000
    mock_span.attributes = None
    mock_status_code = Mock()
    mock_status_code.name = "OK"
    mock_span.status = Mock(status_code=mock_status_code)
    mock_span.events = []
    mock_span.links = []

    exporter = _JSONSpanExporter()
    result = exporter.export([mock_span])

    assert result.name == "FAILURE"


@patch("lilypad._configure.time.time")
@patch("lilypad._configure.get_sync_client")
@patch("lilypad._configure.get_settings")
def test_export_connection_error_suppression(mock_get_settings, mock_get_client, mock_time):
    """Test that connection errors are suppressed after the first occurrence."""
    mock_get_settings.return_value = Mock(api_key="test-key", project_id="test-project", timeout=3.0)

    # Mock time to control error suppression
    mock_time.side_effect = [
        0.0,
        100.0,
        200.0,
        400.0,
    ]  # First error, second error (suppressed), third error (suppressed), fourth error (not suppressed)

    # Mock client to raise connection error
    mock_client = Mock()
    mock_client.projects.traces.create.side_effect = httpx.ConnectError("[Errno -2] Name or service not known")
    mock_get_client.return_value = mock_client

    # Create minimal mock span
    def create_mock_span():
        mock_span = Mock()
        mock_span.context = Mock(trace_id=123, span_id=456)
        mock_span.parent = None
        mock_span.instrumentation_scope = None
        mock_span.resource = Mock()
        mock_span.resource.to_json.return_value = {}
        mock_span.name = "test"
        mock_span.start_time = 1000
        mock_span.end_time = 2000
        mock_span.attributes = None
        mock_status_code = Mock()
        mock_status_code.name = "OK"
        mock_span.status = Mock(status_code=mock_status_code)
        mock_span.events = []
        mock_span.links = []
        return mock_span

    exporter = _JSONSpanExporter()

    # Capture log output
    with patch.object(exporter.log, "error") as mock_error, patch.object(exporter.log, "debug") as mock_debug:
        # First error - should log error
        result1 = exporter.export([create_mock_span()])
        assert result1.name == "FAILURE"
        assert mock_error.call_count == 1
        assert "Network error sending spans to Lilypad server" in mock_error.call_args[0][0]
        assert "LLM calls will continue to work" in mock_error.call_args[0][0]

        # Second error within suppression window - should only log debug
        result2 = exporter.export([create_mock_span()])
        assert result2.name == "FAILURE"
        assert mock_error.call_count == 1  # No new error log
        assert mock_debug.call_count >= 1

        # Third error within suppression window - should only log debug
        result3 = exporter.export([create_mock_span()])
        assert result3.name == "FAILURE"
        assert mock_error.call_count == 1  # Still no new error log

        # Fourth error after suppression window - should log error again
        result4 = exporter.export([create_mock_span()])
        assert result4.name == "FAILURE"
        assert mock_error.call_count == 2  # New error log


@patch("lilypad._configure.get_sync_client")
@patch("lilypad._configure.get_settings")
def test_export_connection_error_reset_on_success(mock_get_settings, mock_get_client):
    """Test that error count is reset after successful connection."""
    mock_get_settings.return_value = Mock(
        api_key="test-key", project_id="test-project", remote_client_url="https://app.lilypad.com", timeout=3.0
    )

    # Mock client to first fail, then succeed
    mock_response = Mock(trace_status="queued", span_count=1, trace_ids=["trace-1"])
    mock_client = Mock()
    mock_client.projects.traces.create.side_effect = [
        OSError(-2, "Name or service not known"),
        mock_response,  # Success
    ]
    mock_get_client.return_value = mock_client

    # Create minimal mock span
    def create_mock_span():
        mock_span = Mock()
        mock_span.context = Mock(trace_id=123, span_id=456)
        mock_span.parent = None
        mock_span.instrumentation_scope = None
        mock_span.resource = Mock()
        mock_span.resource.to_json.return_value = {}
        mock_span.name = "test"
        mock_span.start_time = 1000
        mock_span.end_time = 2000
        mock_span.attributes = None
        mock_status_code = Mock()
        mock_status_code.name = "OK"
        mock_span.status = Mock(status_code=mock_status_code)
        mock_span.events = []
        mock_span.links = []
        return mock_span

    exporter = _JSONSpanExporter()

    # First call fails
    result1 = exporter.export([create_mock_span()])
    assert result1.name == "FAILURE"
    assert exporter._connection_error_count == 1

    # Second call succeeds - error count should reset
    result2 = exporter.export([create_mock_span()])
    assert result2.name == "SUCCESS"
    assert exporter._connection_error_count == 0


@patch("lilypad._configure.get_sync_client")
@patch("lilypad._configure.get_settings")
def test_export_timeout_error(mock_get_settings, mock_get_client):
    """Test that timeout errors are properly handled."""
    mock_get_settings.return_value = Mock(api_key="test-key", project_id="test-project", timeout=10.0)
    
    # Mock client to raise timeout error
    mock_client = Mock()
    mock_client.projects.traces.create.side_effect = httpx.ConnectTimeout("Request timed out")
    mock_get_client.return_value = mock_client

    # Create minimal mock span
    mock_span = Mock()
    mock_span.context = Mock(trace_id=123, span_id=456)
    mock_span.parent = None
    mock_span.instrumentation_scope = None
    mock_span.resource = Mock()
    mock_span.resource.to_json.return_value = {}
    mock_span.name = "test"
    mock_span.start_time = 1000
    mock_span.end_time = 2000
    mock_span.attributes = None
    mock_status_code = Mock()
    mock_status_code.name = "OK"
    mock_span.status = Mock(status_code=mock_status_code)
    mock_span.events = []
    mock_span.links = []

    exporter = _JSONSpanExporter()
    
    # Should handle timeout gracefully
    with patch.object(exporter.log, 'error') as mock_error:
        result = exporter.export([mock_span])
        
        assert result.name == "FAILURE"
        assert mock_error.call_count == 1
        assert "Network error sending spans to Lilypad server" in mock_error.call_args[0][0]
        assert "LLM calls will continue to work" in mock_error.call_args[0][0]


def test_shutdown():
    """Test exporter shutdown."""
    with patch("lilypad._configure.get_sync_client"), patch("lilypad._configure.get_settings"):
        exporter = _JSONSpanExporter()
        # Should not raise any exceptions
        exporter.shutdown()


def test_force_flush():
    """Test exporter force flush."""
    with patch("lilypad._configure.get_sync_client"), patch("lilypad._configure.get_settings"):
        exporter = _JSONSpanExporter()
        assert exporter.force_flush() is True
        assert exporter.force_flush(5000) is True


@pytest.fixture(autouse=True)
def reset_tracer_provider():
    """Reset tracer provider before each test."""
    # Reset to default tracer provider
    trace._TRACER_PROVIDER = None


@patch("lilypad._configure._set_settings")
@patch("lilypad._configure.get_settings")
def test_configure_basic(mock_get_settings, mock_set_settings):
    """Test basic configuration."""
    mock_current = Mock(api_key="old-key", project_id="old-project", base_url="old-url")
    mock_get_settings.return_value = mock_current

    # Mock model_copy to return a new instance
    mock_new = Mock(update=Mock(), api_key="new-key", project_id="new-project", base_url="new-url")
    mock_current.model_copy.return_value = mock_new

    configure(api_key="new-key", project_id="new-project", base_url="new-url")

    mock_current.model_copy.assert_called_once_with(deep=True)
    mock_new.update.assert_called_once_with(api_key="new-key", project_id="new-project", base_url="new-url")
    mock_set_settings.assert_called_once_with(mock_new)


@patch("lilypad._configure.trace")
def test_configure_tracer_already_initialized(mock_trace):
    """Test configuration when tracer is already initialized."""
    # Mock tracer already initialized
    mock_provider = Mock()
    mock_provider.__class__.__name__ = "TracerProvider"
    mock_trace.get_tracer_provider.return_value = mock_provider

    with (
        patch("lilypad._configure.get_settings"),
        patch("lilypad._configure._set_settings"),
        patch("lilypad._configure.logging.getLogger") as mock_logger,
    ):
        logger_instance = Mock()
        mock_logger.return_value = logger_instance

        configure()

        logger_instance.error.assert_called_once_with("TracerProvider already initialized.")


@patch("lilypad._configure.trace")
@patch("lilypad._configure.TracerProvider")
@patch("lilypad._configure.BatchSpanProcessor")
@patch("lilypad._configure._JSONSpanExporter")
def test_configure_with_logging(mock_exporter_class, mock_processor_class, mock_provider_class, mock_trace):
    """Test configuration with custom logging settings."""
    # Mock not already initialized
    mock_trace.get_tracer_provider.return_value = Mock(__class__=Mock(__name__="DefaultTracerProvider"))

    # Create mock instances
    mock_exporter = Mock()
    mock_processor = Mock()
    mock_provider = Mock()

    mock_exporter_class.return_value = mock_exporter
    mock_processor_class.return_value = mock_processor
    mock_provider_class.return_value = mock_provider

    # Custom log handler
    custom_handler = logging.StreamHandler()

    with patch("lilypad._configure.get_settings"), patch("lilypad._configure._set_settings"):
        configure(log_level=logging.DEBUG, log_format="%(message)s", log_handlers=[custom_handler])

        # Verify tracer setup
        mock_provider_class.assert_called_once()
        mock_processor_class.assert_called_once_with(mock_exporter)
        mock_provider.add_span_processor.assert_called_once_with(mock_processor)
        mock_trace.set_tracer_provider.assert_called_once_with(mock_provider)


@patch("lilypad._configure.importlib.util.find_spec")
@patch("lilypad._configure.trace")
def test_configure_auto_llm(mock_trace, mock_find_spec):
    """Test auto_llm instrumentation."""
    # Mock not already initialized
    mock_trace.get_tracer_provider.return_value = Mock(__class__=Mock(__name__="DefaultTracerProvider"))

    # Mock finding all LLM modules
    def find_spec_side_effect(name):
        if name in [
            "openai",
            "anthropic",
            "azure",
            "azure.ai",
            "azure.ai.inference",
            "google",
            "google.genai",
            "botocore",
            "mistralai",
            "outlines",
        ]:
            return Mock()  # Module found
        return None

    mock_find_spec.side_effect = find_spec_side_effect

    with (
        patch("lilypad._configure.get_settings"),
        patch("lilypad._configure._set_settings"),
        patch("lilypad._configure.TracerProvider"),
        patch("lilypad._configure.BatchSpanProcessor"),
        patch("lilypad._configure._JSONSpanExporter"),
        patch("lilypad._opentelemetry.OpenAIInstrumentor") as mock_openai,
        patch("lilypad._opentelemetry.AnthropicInstrumentor") as mock_anthropic,
        patch("lilypad._opentelemetry.AzureInstrumentor") as mock_azure,
        patch("lilypad._opentelemetry.GoogleGenAIInstrumentor", create=True) as mock_google,
        patch("lilypad._opentelemetry.BedrockInstrumentor") as mock_bedrock,
        patch("lilypad._opentelemetry.MistralInstrumentor", create=True) as mock_mistral,
        patch("lilypad._opentelemetry.OutlinesInstrumentor") as mock_outlines,
    ):
        configure(auto_llm=True)

        # Verify all instrumentors were called
        mock_openai.return_value.instrument.assert_called_once()
        mock_anthropic.return_value.instrument.assert_called_once()
        mock_azure.return_value.instrument.assert_called_once()
        mock_google.return_value.instrument.assert_called_once()
        mock_bedrock.return_value.instrument.assert_called_once()
        mock_mistral.return_value.instrument.assert_called_once()
        mock_outlines.return_value.instrument.assert_called_once()


@patch("lilypad._configure._current_settings")
@patch("lilypad._configure.get_settings")
def test_lilypad_config_context(mock_get_settings, mock_current_settings):
    """Test lilypad_config context manager."""
    # Setup base settings
    base_settings = Mock(api_key="base-key", project_id="base-project")
    mock_get_settings.return_value = base_settings

    # Mock model_copy
    tmp_settings = Mock(update=Mock(), api_key="tmp-key", project_id="tmp-project")
    base_settings.model_copy.return_value = tmp_settings

    # Mock token
    mock_token = "test-token"
    mock_current_settings.set.return_value = mock_token

    # Use context manager
    with lilypad_config(api_key="tmp-key", project_id="tmp-project"):
        base_settings.model_copy.assert_called_once_with(deep=True)
        tmp_settings.update.assert_called_once_with(api_key="tmp-key", project_id="tmp-project")
        mock_current_settings.set.assert_called_once_with(tmp_settings)

    # Verify reset was called
    mock_current_settings.reset.assert_called_once_with(mock_token)


@patch("lilypad._configure._current_settings")
@patch("lilypad._configure.get_settings")
def test_lilypad_config_exception(mock_get_settings, mock_current_settings):
    """Test lilypad_config handles exceptions properly."""
    base_settings = Mock()
    tmp_settings = Mock(update=Mock())
    base_settings.model_copy.return_value = tmp_settings
    mock_get_settings.return_value = base_settings

    mock_token = "test-token"
    mock_current_settings.set.return_value = mock_token

    # Test exception handling
    with pytest.raises(ValueError), lilypad_config(api_key="test"):
        raise ValueError("Test error")

    # Verify reset was still called
    mock_current_settings.reset.assert_called_once_with(mock_token)


@patch("lilypad._configure._current_settings")
@patch("lilypad._configure.get_settings")
def test_lilypad_config_no_token(mock_get_settings, mock_current_settings):
    """Test lilypad_config when token is None."""
    base_settings = Mock()
    mock_get_settings.return_value = base_settings

    # Set returns None
    mock_current_settings.set.return_value = None

    with lilypad_config():
        pass

    # Reset should not be called when token is None
    mock_current_settings.reset.assert_not_called()


@patch("lilypad._configure.get_sync_client")
@patch("lilypad._configure.get_settings")
def test_span_to_dict_full(mock_get_settings, mock_get_client):
    """Test converting a fully populated span to dict."""
    mock_get_settings.return_value = Mock(api_key="test-key")
    exporter = _JSONSpanExporter()

    # Create a comprehensive mock span
    mock_span = Mock()
    mock_span.context = Mock(trace_id=0x123456789ABCDEF0, span_id=0xFEDCBA98)
    mock_span.parent = Mock(span_id=0x12345678)
    mock_span.instrumentation_scope = Mock(
        name="test-scope",
        version="1.0.0",
        schema_url="https://example.com/schema",
        attributes=Mock(items=lambda: [("scope.attr", "value")]),
    )
    mock_span.resource = Mock()
    mock_span.resource.to_json.return_value = {"service.name": "test-service"}
    mock_span.name = "test-operation"
    mock_span.start_time = 1609459200000000000  # nanoseconds
    mock_span.end_time = 1609459201000000000
    mock_span.attributes = Mock(
        items=lambda: [("http.method", "GET"), ("http.url", "https://example.com")],
        get=lambda k: "session-123" if k == "lilypad.session_id" else None,
    )
    mock_status_code = Mock()
    mock_status_code.name = "OK"
    mock_span.status = Mock(status_code=mock_status_code)

    # Add events
    mock_event = Mock()
    mock_event.name = "test-event"
    mock_event.attributes = Mock(items=lambda: [("event.data", "test")])
    mock_event.timestamp = 1609459200500000000
    mock_span.events = [mock_event]

    # Add links
    mock_link = Mock(context=Mock(trace_id=0xABCDEF1234567890, span_id=0x87654321), attributes={"link.type": "child"})
    mock_span.links = [mock_link]

    result = exporter._span_to_dict(mock_span)

    assert result["trace_id"] == "0000000000000000123456789abcdef0"
    assert result["span_id"] == "00000000fedcba98"
    assert result["parent_span_id"] == "0000000012345678"
    assert result["name"] == "test-operation"
    assert result["start_time"] == 1609459200000000000
    assert result["end_time"] == 1609459201000000000
    assert result["attributes"] == {"http.method": "GET", "http.url": "https://example.com"}
    assert result["status"] == "OK"
    assert result["session_id"] == "session-123"
    assert len(result["events"]) == 1
    assert result["events"][0]["name"] == "test-event"
    assert len(result["links"]) == 1
    assert result["links"][0]["context"]["trace_id"] == "0000000000000000abcdef1234567890"


@patch("lilypad._configure.get_sync_client")
@patch("lilypad._configure.get_settings")
def test_span_to_dict_minimal(mock_get_settings, mock_get_client):
    """Test converting a minimal span to dict."""
    mock_get_settings.return_value = Mock(api_key="test-key")
    exporter = _JSONSpanExporter()

    # Create a minimal mock span
    mock_span = Mock()
    mock_span.context = None
    mock_span.parent = None
    mock_span.instrumentation_scope = None
    mock_span.resource = Mock()
    mock_span.resource.to_json.return_value = {}
    mock_span.name = "minimal-span"
    mock_span.start_time = 1000
    mock_span.end_time = 2000
    mock_span.attributes = None
    mock_status_code = Mock()
    mock_status_code.name = "UNSET"
    mock_span.status = Mock(status_code=mock_status_code)
    mock_span.events = []
    mock_span.links = []

    result = exporter._span_to_dict(mock_span)

    assert result["trace_id"] is None
    assert result["span_id"] is None
    assert result["parent_span_id"] is None
    assert result["name"] == "minimal-span"
    assert result["attributes"] == {}
    assert result["session_id"] is None
    assert result["events"] == []
    assert result["links"] == []
    assert result["instrumentation_scope"]["name"] is None


@patch("lilypad._configure.get_sync_client")
@patch("lilypad._configure.get_settings")
def test_export_with_custom_timeout(mock_get_settings, mock_get_client):
    """Test that custom timeout from settings is used."""
    mock_settings = Mock(api_key="test-key", project_id="test-project", timeout=10.0)
    mock_get_settings.return_value = mock_settings

    exporter = _JSONSpanExporter()

    assert exporter.settings == mock_settings
    mock_get_client.assert_called_once_with(api_key="test-key", timeout=10.0)


def test_settings_timeout_default():
    """Test that Settings has correct default timeout (OpenTelemetry standard)."""
    settings = Settings()
    assert settings.timeout == 10.0


@patch.dict(os.environ, {"LILYPAD_TIMEOUT": "15.0"}, clear=False)
def test_settings_timeout_from_env():
    """Test that timeout can be set from environment variable."""
    # Clear the cache to ensure we get a fresh Settings instance
    from lilypad._utils.settings import _default_settings

    _default_settings.cache_clear()

    settings = Settings()
    assert settings.timeout == 15.0

    # Clear cache again after test
    _default_settings.cache_clear()
