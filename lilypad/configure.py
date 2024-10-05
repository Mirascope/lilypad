import importlib.util

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .exporter import JSONSpanExporter


def init():
    trace_url = "http://localhost:8000/api/v1/traces"

    otlp_exporter = JSONSpanExporter(
        endpoint=trace_url,
    )

    provider = TracerProvider()
    processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    if importlib.util.find_spec("opentelemetry.instrumentation.openai") is not None:
        from opentelemetry.instrumentation.openai import OpenAIInstrumentor

        # Now that it is confirmed to be available, you can use it
        OpenAIInstrumentor().instrument()
        print("OpenAIInstrumentor successfully instrumented.")
    else:
        print("opentelemetry.instrumentation.openai is not installed or available.")
