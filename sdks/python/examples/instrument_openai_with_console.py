import lilypad
from openai import OpenAI
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

client = OpenAI()
lilypad.instrument_openai(client)

completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}],
)

print(completion.choices[0].message.content)
