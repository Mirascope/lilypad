import os

import lilypad
from mistralai import Mistral
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

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
lilypad.instrument_mistral(client)

completion = client.chat.complete(
    model="mistral-small-latest",
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=50,
    stream=True
)

content = completion.choices[0].message.content
print(content)