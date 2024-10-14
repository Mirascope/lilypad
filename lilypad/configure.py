"""Initialize Lilypad OpenTelemetry instrumentation."""

import importlib.util
import os

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from lilypad.exporter import JSONSpanExporter


def configure() -> None:
    """Initialize the OpenTelemetry instrumentation for Lilypad."""
    if trace.get_tracer_provider().__class__.__name__ == "TracerProvider":
        print("TracerProvider already initialized.")  # noqa: T201
        return

    port = os.environ.get("LILYPAD_BACKEND_PORT", "8000")
    otlp_exporter = JSONSpanExporter(
        base_url=f"http://127.0.0.1:{port}/api",
    )

    provider = TracerProvider()
    processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

    if importlib.util.find_spec("opentelemetry.instrumentation.openai") is not None:
        from opentelemetry.instrumentation.openai import OpenAIInstrumentor

        OpenAIInstrumentor().instrument()

    if importlib.util.find_spec("opentelemetry.instrumentation.anthropic") is not None:
        from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor

        AnthropicInstrumentor().instrument()
