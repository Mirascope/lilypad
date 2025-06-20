"""Tests for context managers module."""

from unittest.mock import Mock, patch
import pytest
from opentelemetry import context as otel_context

from lilypad import propagated_context


def test_propagated_context_extracts_and_attaches_from_headers():
    """Test that context extracts and attaches context from headers."""
    # Mock headers with trace context
    headers = {"traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"}

    # Mock the extract_context function
    mock_context = Mock()
    mock_token = Mock()

    with (
        patch("lilypad.context_managers._extract_context") as mock_extract,
        patch.object(otel_context, "attach") as mock_attach,
        patch.object(otel_context, "detach") as mock_detach,
    ):
        mock_extract.return_value = mock_context
        mock_attach.return_value = mock_token

        # Use the context manager
        with propagated_context(extract_from=headers):
            # Verify context was extracted
            mock_extract.assert_called_once_with(headers)
            # Verify context was attached
            mock_attach.assert_called_once_with(mock_context)

        # Verify context was detached after exit
        mock_detach.assert_called_once_with(mock_token)


def test_propagated_context_with_empty_headers():
    """Test context with empty headers."""
    headers = {}
    mock_context = Mock()
    mock_token = Mock()

    with (
        patch("lilypad.context_managers._extract_context") as mock_extract,
        patch.object(otel_context, "attach") as mock_attach,
        patch.object(otel_context, "detach") as mock_detach,
    ):
        mock_extract.return_value = mock_context
        mock_attach.return_value = mock_token

        # Test that context manager works with empty headers
        # The context manager should still process empty headers since {} is truthy
        with propagated_context(extract_from=headers):
            # Verify extract was called even with empty headers
            mock_extract.assert_called_once_with(headers)
            # Verify context was attached
            mock_attach.assert_called_once_with(mock_context)

        # Verify context was detached after exit
        mock_detach.assert_called_once_with(mock_token)


def test_propagated_context_detaches_on_exception_with_extract_from():
    """Test that context is detached even if exception occurs."""
    headers = {"traceparent": "00-test-test-01"}
    mock_token = Mock()
    mock_context = Mock()

    with (
        patch("lilypad.context_managers._extract_context") as mock_extract,
        patch.object(otel_context, "attach", return_value=mock_token),
        patch.object(otel_context, "detach") as mock_detach,
    ):
        mock_extract.return_value = mock_context

        # Use pytest.raises properly - it should wrap the context manager
        with pytest.raises(ValueError), propagated_context(extract_from=headers):
            raise ValueError("test error")

        # Context should still be detached
        mock_detach.assert_called_once_with(mock_token)


def test_propagated_context_with_parent():
    """Test context manager with parent context."""
    parent_ctx = Mock()
    mock_token = Mock()

    with (
        patch.object(otel_context, "attach") as mock_attach,
        patch.object(otel_context, "detach") as mock_detach,
    ):
        mock_attach.return_value = mock_token

        with propagated_context(parent=parent_ctx):
            mock_attach.assert_called_once_with(parent_ctx)

        mock_detach.assert_called_once_with(mock_token)


def test_propagated_context_with_extract_from():
    """Test context manager with extract_from."""
    headers = {"traceparent": "00-test-test-01"}
    mock_context = Mock()
    mock_token = Mock()

    with (
        patch("lilypad.context_managers._extract_context") as mock_extract,
        patch.object(otel_context, "attach") as mock_attach,
        patch.object(otel_context, "detach") as mock_detach,
    ):
        mock_extract.return_value = mock_context
        mock_attach.return_value = mock_token

        with propagated_context(extract_from=headers):
            mock_extract.assert_called_once_with(headers)
            mock_attach.assert_called_once_with(mock_context)

        mock_detach.assert_called_once_with(mock_token)


def test_propagated_context_with_both_raises_error():
    """Test that providing both parent and extract_from raises error."""
    parent_ctx = Mock()
    headers = {"traceparent": "00-test-test-01"}

    with (
        pytest.raises(ValueError, match="Cannot specify both parent and extract_from"),
        propagated_context(parent=parent_ctx, extract_from=headers),
    ):
        pass


def test_propagated_context_with_neither_parameter():
    """Test context manager with neither parameter."""
    with (
        patch.object(otel_context, "attach") as mock_attach,
        patch.object(otel_context, "detach") as mock_detach,
    ):
        with propagated_context():
            # Should not attach anything
            mock_attach.assert_not_called()

        # Should not detach anything
        mock_detach.assert_not_called()


def test_propagated_context_detaches_on_exception_with_parent():
    """Test that context is detached on exception with parent."""
    parent_ctx = Mock()
    mock_token = Mock()

    with (
        patch.object(otel_context, "attach", return_value=mock_token),
        patch.object(otel_context, "detach") as mock_detach,
    ):
        # Use pytest.raises properly - it should wrap the context manager
        with pytest.raises(ValueError), propagated_context(parent=parent_ctx):
            raise ValueError("test error")

        mock_detach.assert_called_once_with(mock_token)


def test_propagated_context_none_token_not_detached():
    """Test that None token is not detached."""
    # When no context is attached, token would be None
    with (
        patch.object(otel_context, "attach") as mock_attach,
        patch.object(otel_context, "detach") as mock_detach,
    ):
        mock_attach.return_value = None

        with propagated_context():
            pass

        # detach should not be called with None
        mock_detach.assert_not_called()
