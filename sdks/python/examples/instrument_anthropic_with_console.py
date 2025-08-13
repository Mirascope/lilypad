import lilypad
from anthropic import Anthropic
from anthropic.types import TextBlock
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

client = Anthropic()
lilypad.instrument_anthropic(client)

message = client.messages.create(
    model="claude-3-haiku-20240307",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello! How are you?"}],
)
if (content := message.content) and isinstance(content[0], TextBlock):
    print(content[0].text)
else:
    print("No content found.")