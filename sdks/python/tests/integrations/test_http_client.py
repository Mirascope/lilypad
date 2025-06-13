"""Tests for HTTP client integrations."""

import pytest
from unittest.mock import Mock, patch

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider


@pytest.fixture
def setup_tracer():
    """Set up a test tracer provider."""
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    yield provider
    # Clean up
    trace.set_tracer_provider(None)


class TestRequestsIntegration:
    """Test requests library integration."""

    @pytest.mark.skipif(not pytest.importorskip("requests"), reason="requests not installed")
    def test_traced_requests_session(self, setup_tracer):
        """Test TracedRequestsSession injects headers."""
        from lilypad.integrations.http_client import TracedRequestsSession

        tracer = trace.get_tracer(__name__)

        with (
            tracer.start_as_current_span("test_span") as span,
            patch("requests.Session.request") as mock_request,
        ):
            mock_request.return_value = Mock()

            session = TracedRequestsSession()
            session.get("http://example.com")

            # Verify request was called with headers
            mock_request.assert_called_once()
            args, kwargs = mock_request.call_args

            # Check that traceparent header was injected
            assert "headers" in kwargs
            assert "traceparent" in kwargs["headers"]

            # Verify the trace ID matches
            trace_id = format(span.get_span_context().trace_id, "032x")
            assert trace_id in kwargs["headers"]["traceparent"]

    @pytest.mark.skipif(not pytest.importorskip("requests"), reason="requests not installed")
    def test_traced_requests_get_convenience(self, setup_tracer):
        """Test traced_requests_get convenience function."""
        from lilypad.integrations.http_client import traced_requests_get

        tracer = trace.get_tracer(__name__)

        with (
            tracer.start_as_current_span("test_span"),
            patch("lilypad.integrations.http_client.TracedRequestsSession.get") as mock_get,
        ):
            mock_get.return_value = Mock()

            traced_requests_get("http://example.com", params={"q": "test"})

            mock_get.assert_called_once_with("http://example.com", params={"q": "test"})


class TestHTTPXIntegration:
    """Test httpx library integration."""

    @pytest.mark.skipif(not pytest.importorskip("httpx"), reason="httpx not installed")
    def test_traced_httpx_client(self, setup_tracer):
        """Test TracedHTTPXClient injects headers."""
        from lilypad.integrations.http_client import TracedHTTPXClient

        tracer = trace.get_tracer(__name__)

        with (
            tracer.start_as_current_span("test_span") as span,
            patch("httpx.Client.request") as mock_request,
        ):
            mock_request.return_value = Mock()

            with TracedHTTPXClient() as client:
                client.get("http://example.com")

            # Verify request was called with headers
            mock_request.assert_called_once()
            args, kwargs = mock_request.call_args

            # Check that traceparent header was injected
            assert "headers" in kwargs
            assert "traceparent" in kwargs["headers"]

            # Verify the trace ID matches
            trace_id = format(span.get_span_context().trace_id, "032x")
            assert trace_id in kwargs["headers"]["traceparent"]

    @pytest.mark.skipif(not pytest.importorskip("httpx"), reason="httpx not installed")
    @pytest.mark.asyncio
    async def test_traced_async_httpx_client(self, setup_tracer):
        """Test TracedAsyncHTTPXClient injects headers."""
        from lilypad.integrations.http_client import TracedAsyncHTTPXClient

        tracer = trace.get_tracer(__name__)

        with (
            tracer.start_as_current_span("test_span") as span,
            patch("httpx.AsyncClient.request") as mock_request,
        ):
            mock_response = Mock()
            mock_request.return_value = mock_response

            async with TracedAsyncHTTPXClient() as client:
                await client.get("http://example.com")

            # Verify request was called with headers
            mock_request.assert_called_once()
            args, kwargs = mock_request.call_args

            # Check that traceparent header was injected
            assert "headers" in kwargs
            assert "traceparent" in kwargs["headers"]

            # Verify the trace ID matches
            trace_id = format(span.get_span_context().trace_id, "032x")
            assert trace_id in kwargs["headers"]["traceparent"]


class TestAiohttpIntegration:
    """Test aiohttp library integration."""

    @pytest.mark.skipif(not pytest.importorskip("aiohttp"), reason="aiohttp not installed")
    @pytest.mark.asyncio
    async def test_traced_aiohttp_session(self, setup_tracer):
        """Test TracedAiohttpSession injects headers."""
        from lilypad.integrations.http_client import TracedAiohttpSession

        tracer = trace.get_tracer(__name__)

        with (
            tracer.start_as_current_span("test_span") as span,
            patch("aiohttp.ClientSession._request") as mock_request,
        ):
            mock_response = Mock()
            mock_request.return_value = mock_response

            async with TracedAiohttpSession() as session:
                await session.get("http://example.com")

            # Verify request was called with headers
            mock_request.assert_called_once()
            args, kwargs = mock_request.call_args

            # Check that traceparent header was injected
            assert "headers" in kwargs
            assert "traceparent" in kwargs["headers"]

            # Verify the trace ID matches
            trace_id = format(span.get_span_context().trace_id, "032x")
            assert trace_id in kwargs["headers"]["traceparent"]


class TestGetTracedHTTPClient:
    """Test the get_traced_http_client convenience function."""

    def test_get_sync_client_with_requests(self):
        """Test getting sync client when requests is available."""
        with (
            patch("lilypad.integrations.http_client._HAS_REQUESTS", True),
            patch("lilypad.integrations.http_client._HAS_HTTPX", False),
        ):
            from lilypad.integrations.http_client import get_traced_http_client

            client = get_traced_http_client(async_client=False)
            assert "TracedRequestsSession" in str(type(client))

    def test_get_sync_client_with_httpx(self):
        """Test getting sync client when httpx is available."""
        with (
            patch("lilypad.integrations.http_client._HAS_REQUESTS", False),
            patch("lilypad.integrations.http_client._HAS_HTTPX", True),
        ):
            from lilypad.integrations.http_client import get_traced_http_client

            client = get_traced_http_client(async_client=False)
            assert "TracedHTTPXClient" in str(type(client))

    def test_get_async_client_with_httpx(self):
        """Test getting async client when httpx is available."""
        with (
            patch("lilypad.integrations.http_client._HAS_HTTPX", True),
            patch("lilypad.integrations.http_client._HAS_AIOHTTP", False),
        ):
            from lilypad.integrations.http_client import get_traced_http_client

            client_factory = get_traced_http_client(async_client=True)
            # For async clients, we return a factory function
            assert callable(client_factory)
            # Create an instance to verify it works
            client = client_factory()
            assert "TracedAsyncHTTPXClient" in str(type(client))

    def test_get_async_client_with_aiohttp(self):
        """Test getting async client when aiohttp is available."""
        with (
            patch("lilypad.integrations.http_client._HAS_HTTPX", False),
            patch("lilypad.integrations.http_client._HAS_AIOHTTP", True),
        ):
            from lilypad.integrations.http_client import get_traced_http_client

            client_factory = get_traced_http_client(async_client=True)
            # For async clients, we return a factory function
            assert callable(client_factory)
            assert "create_traced_aiohttp_session" in str(client_factory)

    def test_no_client_available_error(self):
        """Test error when no HTTP client library is available."""
        with (
            patch("lilypad.integrations.http_client._HAS_REQUESTS", False),
            patch("lilypad.integrations.http_client._HAS_HTTPX", False),
            patch("lilypad.integrations.http_client._HAS_AIOHTTP", False),
        ):
            from lilypad.integrations.http_client import get_traced_http_client

            with pytest.raises(ImportError, match="No.*HTTP client library found"):
                get_traced_http_client(async_client=False)

            with pytest.raises(ImportError, match="No async HTTP client library found"):
                get_traced_http_client(async_client=True)

    @patch.dict("os.environ", {"LILYPAD_HTTP_CLIENT": "httpx"})
    def test_preference_from_environment(self):
        """Test client preference from environment variable."""
        with (
            patch("lilypad.integrations.http_client._HAS_REQUESTS", True),
            patch("lilypad.integrations.http_client._HAS_HTTPX", True),
        ):
            from lilypad.integrations.http_client import get_traced_http_client

            # Should prefer httpx due to environment variable
            client = get_traced_http_client(async_client=False)
            assert "TracedHTTPXClient" in str(type(client))
