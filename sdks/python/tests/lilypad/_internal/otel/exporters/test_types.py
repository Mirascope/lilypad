"""Simple test to verify imports work."""


def test_import_transport():
    """Test that transport module can be imported."""
    from lilypad._internal.otel.exporters.transport import TelemetryTransport

    assert TelemetryTransport is not None


def test_import_exporters():
    """Test that exporters module can be imported."""
    from lilypad._internal.otel.exporters.exporters import LilypadOTLPExporter

    assert LilypadOTLPExporter is not None


def test_import_processors():
    """Test that processors module can be imported."""
    from lilypad._internal.otel.exporters.processors import LLMSpanProcessor

    assert LLMSpanProcessor is not None


def test_import_config():
    """Test that config module can be imported."""
    from lilypad._internal.otel.exporters.config import ConfigureExportersConfig

    assert ConfigureExportersConfig is not None


def test_import_client():
    """Test that client module can be imported."""
    from lilypad.client import get_client

    assert get_client is not None
