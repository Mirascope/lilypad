import logging
from unittest.mock import Mock, MagicMock, patch
import pytest
from opentelemetry import trace
from opentelemetry.trace import INVALID_SPAN_ID, INVALID_TRACE_ID
from opentelemetry.sdk.trace import TracerProvider

from lilypad.configuration import CryptoIdGenerator, configure


@pytest.fixture(autouse=True)
def clear_logger_handlers():
    """Clear logger handlers after each test to prevent test pollution."""
    yield
    logger = logging.getLogger("lilypad")
    logger.handlers.clear()
    logger.setLevel(logging.WARNING)


def test_generate_span_id() -> None:
    generator = CryptoIdGenerator()

    span_ids = [generator.generate_span_id() for _ in range(100)]

    assert len(set(span_ids)) == 100
    assert all(sid != INVALID_SPAN_ID for sid in span_ids)
    assert all(0 < sid < 2**64 for sid in span_ids)


def test_generate_trace_id() -> None:
    generator = CryptoIdGenerator()

    trace_ids = [generator.generate_trace_id() for _ in range(100)]

    assert len(set(trace_ids)) == 100
    assert all(tid != INVALID_TRACE_ID for tid in trace_ids)
    assert all(0 < tid < 2**128 for tid in trace_ids)


@patch("lilypad.configuration.token_bytes")
def test_regenerate_invalid_span_id(mock_token_bytes: MagicMock) -> None:
    generator = CryptoIdGenerator()

    mock_token_bytes.side_effect = [
        b"\x00" * 8,
        b"\x00" * 7 + b"\x01",
    ]

    span_id = generator.generate_span_id()
    assert span_id != INVALID_SPAN_ID
    assert mock_token_bytes.call_count == 2


@patch("lilypad.configuration.token_bytes")
def test_regenerate_invalid_trace_id(mock_token_bytes: MagicMock) -> None:
    generator = CryptoIdGenerator()

    mock_token_bytes.side_effect = [
        b"\x00" * 16,
        b"\x00" * 15 + b"\x01",
    ]

    trace_id = generator.generate_trace_id()
    assert trace_id != INVALID_TRACE_ID
    assert mock_token_bytes.call_count == 2


def test_configure_already_initialized(caplog: pytest.LogCaptureFixture) -> None:
    original_provider = trace.get_tracer_provider()
    try:
        provider = TracerProvider()
        trace.set_tracer_provider(provider)

        with caplog.at_level(logging.INFO):
            configure()

        assert "TracerProvider already initialized." in caplog.text
    finally:
        trace._TRACER_PROVIDER = original_provider


def test_configure_custom_log_handlers() -> None:
    custom_handler = logging.StreamHandler()
    configure(log_handlers=[custom_handler])

    logger = logging.getLogger("lilypad")
    assert custom_handler in logger.handlers


def test_configure_custom_log_format() -> None:
    custom_format = "%(levelname)s - %(message)s"
    custom_handler = logging.StreamHandler()
    configure(log_format=custom_format, log_handlers=[custom_handler])

    logger = logging.getLogger("lilypad")
    handler = logger.handlers[0]
    assert handler.formatter is not None
    assert handler.formatter._fmt == custom_format


def test_configure_custom_log_level() -> None:
    configure(log_level=logging.DEBUG)

    logger = logging.getLogger("lilypad")
    assert logger.level == logging.DEBUG


def test_configure_with_rich_handler() -> None:
    with patch("lilypad.configuration.RichHandler") as mock_rich_handler:
        mock_handler = Mock()
        mock_handler.level = logging.INFO
        mock_rich_handler.return_value = mock_handler

        configure()

        mock_rich_handler.assert_called_once()
        logger = logging.getLogger("lilypad")
        assert mock_handler in logger.handlers


def test_configure_without_rich_handler() -> None:
    custom_handler = logging.StreamHandler()
    configure(log_handlers=[custom_handler])

    logger = logging.getLogger("lilypad")
    assert len(logger.handlers) == 1
    assert custom_handler in logger.handlers
