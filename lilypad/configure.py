"""Initialize Lilypad OpenTelemetry instrumentation."""

import importlib.util

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from lilypad.exporter import JSONSpanExporter


def init():
    """Initialize the OpenTelemetry instrumentation for Lilypad."""
    if trace.get_tracer_provider().__class__.__name__ == "TracerProvider":
        print("TracerProvider already initialized.")
        return

    otlp_exporter = JSONSpanExporter(
        base_url="http://127.0.0.1:8000/api",
    )

    provider = TracerProvider()
    processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    if importlib.util.find_spec("opentelemetry.instrumentation.openai") is not None:
        from opentelemetry.instrumentation.openai import OpenAIInstrumentor

        OpenAIInstrumentor().instrument()
        print("OpenAIInstrumentor initialized.")
    else:
        print("opentelemetry.instrumentation.openai is not installed or available.")
