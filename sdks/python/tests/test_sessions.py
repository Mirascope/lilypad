import re
from unittest.mock import MagicMock, patch

import pytest
from opentelemetry.sdk.trace import TracerProvider

from lilypad.spans import span
from lilypad.sessions import SESSION_CONTEXT, Session, session


class DummyTracer:
    """Tracer that stores the last span it created."""

    def __init__(self) -> None:
        self.last_span = None

    def start_span(self, name):
        mock = MagicMock()
        mock.parent = None
        mock.get_span_context.return_value.span_id = 1
        self.last_span = mock
        return mock


def test_generate_id_format():
    sid = Session.generate_id()
    assert re.fullmatch(r"[0-9a-f]{32}", sid)


@pytest.mark.parametrize(
    "args, expect_none",
    [((), False), ((None,), True), (("fixed-id",), False)],
)
def test_run_context_set_and_reset(args, expect_none):
    assert SESSION_CONTEXT.get() is None
    with session(*args) as r:
        assert SESSION_CONTEXT.get() is r
        assert (r.id is None) == expect_none
    assert SESSION_CONTEXT.get() is None


def test_span_writes_run_id():
    tracer = DummyTracer()

    # Create a mock that properly inherits from TracerProvider
    class MockTracerProvider(TracerProvider):
        pass

    with (
        patch("lilypad.spans.get_tracer", lambda *_: tracer),
        patch("lilypad.spans.get_tracer_provider", lambda: MockTracerProvider()),
        session(id="my-session-id"),
        span("test-span"),
    ):
        pass  # span exits

    created = tracer.last_span
    created.set_attribute.assert_any_call("lilypad.session_id", "my-session-id")


def test_span_no_run_id_when_none():
    tracer = DummyTracer()

    # Create a mock that properly inherits from TracerProvider
    class MockTracerProvider(TracerProvider):
        pass

    with (
        patch("lilypad.spans.get_tracer", lambda *_: tracer),
        patch("lilypad.spans.get_tracer_provider", lambda: MockTracerProvider()),
        session(id=None),
        span("test-span"),
    ):
        pass  # span exits

    assert not any(
        call_args[0][0] == "lilypad.session_id" for call_args in tracer.last_span.set_attribute.call_args_list
    )
