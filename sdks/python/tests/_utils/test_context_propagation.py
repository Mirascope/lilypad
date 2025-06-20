"""Tests for context propagation utilities."""

import os
from unittest.mock import Mock, patch
import pytest

from lilypad._utils.context_propagation import (
    get_propagator,
    ContextPropagator,
    _extract_context as extract_context,
    _inject_context as inject_context,
    with_extracted_context,
    detach_context,
)


# Tests for get_propagator function
@pytest.fixture(autouse=True)
def clear_env():
    """Clear environment before each test."""
    if "LILYPAD_PROPAGATOR" in os.environ:
        del os.environ["LILYPAD_PROPAGATOR"]


def test_get_propagator_default():
    """Test get_propagator returns tracecontext by default."""
    propagator = get_propagator()
    # Should be a CompositePropagator with TraceContextTextMapPropagator
    assert propagator._propagators is not None
    assert len(propagator._propagators) == 1


def test_get_propagator_b3():
    """Test get_propagator with B3 single format."""
    os.environ["LILYPAD_PROPAGATOR"] = "b3"
    propagator = get_propagator()
    assert propagator._propagators is not None
    assert len(propagator._propagators) == 1


def test_get_propagator_b3multi():
    """Test get_propagator with B3 multi format."""
    os.environ["LILYPAD_PROPAGATOR"] = "b3multi"
    propagator = get_propagator()
    assert propagator._propagators is not None
    assert len(propagator._propagators) == 1


def test_get_propagator_jaeger():
    """Test get_propagator with Jaeger format."""
    os.environ["LILYPAD_PROPAGATOR"] = "jaeger"
    propagator = get_propagator()
    assert propagator._propagators is not None
    assert len(propagator._propagators) == 1


def test_get_propagator_composite():
    """Test get_propagator with composite format."""
    os.environ["LILYPAD_PROPAGATOR"] = "composite"
    propagator = get_propagator()
    assert propagator._propagators is not None
    # Composite should have all 4 propagators
    assert len(propagator._propagators) == 4


def test_get_propagator_unknown():
    """Test get_propagator with unknown format defaults to tracecontext."""
    os.environ["LILYPAD_PROPAGATOR"] = "unknown"
    propagator = get_propagator()
    assert propagator._propagators is not None
    assert len(propagator._propagators) == 1


# Tests for ContextPropagator class
def test_init_sets_global_propagator():
    """Test that ContextPropagator sets global propagator on init."""
    with patch("lilypad._utils.context_propagation.propagate.set_global_textmap") as mock_set:
        propagator = ContextPropagator()
        mock_set.assert_called_once_with(propagator.propagator)


def test_extract_context():
    """Test extract_context method."""
    with patch("lilypad._utils.context_propagation.propagate.extract") as mock_extract:
        mock_context = Mock()
        mock_extract.return_value = mock_context

        propagator = ContextPropagator()
        carrier = {"traceparent": "00-test-test-01"}

        result = propagator.extract_context(carrier)

        mock_extract.assert_called_once_with(carrier)
        assert result == mock_context


def test_inject_context_default():
    """Test inject_context with default context."""
    with patch("lilypad._utils.context_propagation.propagate.inject") as mock_inject:
        propagator = ContextPropagator()
        carrier = {}

        propagator.inject_context(carrier)

        mock_inject.assert_called_once_with(carrier, context=None)


def test_inject_context_with_context():
    """Test inject_context with specific context."""
    with patch("lilypad._utils.context_propagation.propagate.inject") as mock_inject:
        propagator = ContextPropagator()
        carrier = {}
        mock_context = Mock()

        propagator.inject_context(carrier, context=mock_context)

        mock_inject.assert_called_once_with(carrier, context=mock_context)


def test_with_extracted_context():
    """Test with_extracted_context method."""
    with patch("lilypad._utils.context_propagation.context.attach") as mock_attach:
        mock_context = Mock()
        mock_token = Mock()
        mock_attach.return_value = mock_token

        propagator = ContextPropagator()
        carrier = {"traceparent": "00-test-test-01"}

        with patch.object(propagator, "extract_context", return_value=mock_context):
            ctx, token = propagator.with_extracted_context(carrier)

            assert ctx == mock_context
            assert token == mock_token
            mock_attach.assert_called_once_with(mock_context)


def test_detach_context():
    """Test detach_context method."""
    with patch("lilypad._utils.context_propagation.context.detach") as mock_detach:
        propagator = ContextPropagator()
        mock_token = Mock()

        propagator.detach_context(mock_token)

        mock_detach.assert_called_once_with(mock_token)


def test_detach_context_none():
    """Test detach_context with None token."""
    with patch("lilypad._utils.context_propagation.context.detach") as mock_detach:
        propagator = ContextPropagator()

        propagator.detach_context(None)

        # Should not call detach with None
        mock_detach.assert_not_called()


# Tests for module-level functions
def test_extract_context_function():
    """Test module-level extract_context function."""
    with patch("lilypad._utils.context_propagation._get_propagator") as mock_get_propagator:
        mock_propagator = Mock()
        mock_context = Mock()
        mock_propagator.extract_context.return_value = mock_context
        mock_get_propagator.return_value = mock_propagator

        carrier = {"traceparent": "00-test-test-01"}
        result = extract_context(carrier)

        mock_propagator.extract_context.assert_called_once_with(carrier)
        assert result == mock_context


def test_inject_context_function():
    """Test module-level inject_context function."""
    with patch("lilypad._utils.context_propagation._get_propagator") as mock_get_propagator:
        mock_propagator = Mock()
        mock_get_propagator.return_value = mock_propagator

        carrier = {}
        inject_context(carrier)

        mock_propagator.inject_context.assert_called_once_with(carrier, None)


def test_inject_context_function_with_context():
    """Test module-level inject_context function with context."""
    with patch("lilypad._utils.context_propagation._get_propagator") as mock_get_propagator:
        mock_propagator = Mock()
        mock_get_propagator.return_value = mock_propagator

        carrier = {}
        mock_context = Mock()

        inject_context(carrier, context=mock_context)

        mock_propagator.inject_context.assert_called_once_with(carrier, mock_context)


def test_with_extracted_context_function():
    """Test module-level with_extracted_context function."""
    with patch("lilypad._utils.context_propagation._get_propagator") as mock_get_propagator:
        mock_propagator = Mock()
        mock_context = Mock()
        mock_token = Mock()
        mock_propagator.with_extracted_context.return_value = (mock_context, mock_token)
        mock_get_propagator.return_value = mock_propagator

        carrier = {"traceparent": "00-test-test-01"}
        ctx, token = with_extracted_context(carrier)

        mock_propagator.with_extracted_context.assert_called_once_with(carrier)
        assert ctx == mock_context
        assert token == mock_token


def test_detach_context_function():
    """Test module-level detach_context function."""
    with patch("lilypad._utils.context_propagation._get_propagator") as mock_get_propagator:
        mock_propagator = Mock()
        mock_get_propagator.return_value = mock_propagator

        mock_token = Mock()

        detach_context(mock_token)

        mock_propagator.detach_context.assert_called_once_with(mock_token)


def test_get_propagator_creates_new_instance():
    """Test _get_propagator creates new instance when _propagator is None."""
    import lilypad._utils.context_propagation as context_prop

    # Save original state
    original_propagator = context_prop._propagator
    original_env = os.environ.get("_LILYPAD_PROPAGATOR_SET_GLOBAL")

    try:
        # Reset _propagator to None to trigger creation
        context_prop._propagator = None

        # Test with default (set_global=True)
        if "_LILYPAD_PROPAGATOR_SET_GLOBAL" in os.environ:
            del os.environ["_LILYPAD_PROPAGATOR_SET_GLOBAL"]

        propagator1 = context_prop._get_propagator()
        assert propagator1 is not None
        assert isinstance(propagator1, ContextPropagator)

        # Reset again and test with set_global=False
        context_prop._propagator = None
        os.environ["_LILYPAD_PROPAGATOR_SET_GLOBAL"] = "false"

        propagator2 = context_prop._get_propagator()
        assert propagator2 is not None
        assert isinstance(propagator2, ContextPropagator)

        # Reset again and test with set_global=true (lowercase)
        context_prop._propagator = None
        os.environ["_LILYPAD_PROPAGATOR_SET_GLOBAL"] = "true"

        propagator3 = context_prop._get_propagator()
        assert propagator3 is not None
        assert isinstance(propagator3, ContextPropagator)

    finally:
        # Restore original state
        context_prop._propagator = original_propagator
        if original_env is not None:
            os.environ["_LILYPAD_PROPAGATOR_SET_GLOBAL"] = original_env
        elif "_LILYPAD_PROPAGATOR_SET_GLOBAL" in os.environ:
            del os.environ["_LILYPAD_PROPAGATOR_SET_GLOBAL"]
