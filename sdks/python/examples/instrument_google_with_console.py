import lilypad
from google import genai
from opentelemetry import trace
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.sdk.trace import TracerProvider

# Export spans to the console.
otlp_exporter = ConsoleSpanExporter()
processor = SimpleSpanProcessor(otlp_exporter)
provider = TracerProvider(id_generator=lilypad.configuration.CryptoIdGenerator())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

lilypad.configure()  # will log that a tracer has already been configured, which is ok

# Initialize Google GenAI client
client = genai.Client()
models = client.models
lilypad.instrument_google(models)

# Non-streaming example
response = models.generate_content(
    model="gemini-2.0-flash-exp",
    contents="Hello! How's it going?",
)

if response.candidates:
    for candidate in response.candidates:
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if hasattr(part, "text"):
                    print(part.text)