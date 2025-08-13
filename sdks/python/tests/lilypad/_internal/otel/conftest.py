"""Common fixtures for OpenTelemetry instrumentation tests.

This module provides shared fixtures that can be used across all OTel test modules.
"""

from typing import Generator

import pytest
from opentelemetry import trace
from opentelemetry.trace import ProxyTracerProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from .test_utils import ReadOnlyPropertyMock, PartialReadOnlyPropertyMock


@pytest.fixture
def readonly_mock():
    """Fixture providing a mock with all read-only properties."""
    return ReadOnlyPropertyMock()


@pytest.fixture
def partial_readonly_mock():
    """Fixture providing a mock with mixed writable and read-only properties."""
    return PartialReadOnlyPropertyMock()


@pytest.fixture
def span_exporter() -> Generator[InMemorySpanExporter, None, None]:
    """Set up InMemorySpanExporter for testing span content.

    Yields:
        InMemorySpanExporter instance that captures spans
    """
    current_provider = trace.get_tracer_provider()
    if isinstance(current_provider, ProxyTracerProvider):
        provider = TracerProvider()
        trace.set_tracer_provider(provider)
    else:
        provider = current_provider
    exporter = InMemorySpanExporter()
    processor = SimpleSpanProcessor(exporter)
    provider.add_span_processor(processor)  # type: ignore[attr-defined]

    exporter.clear()
    yield exporter
    exporter.clear()


__all__ = [
    "partial_readonly_mock",
    "readonly_mock",
    "span_exporter",
]
