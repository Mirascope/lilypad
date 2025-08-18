import os
import lilypad
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
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

# Initialize Azure AI Inference client
endpoint = os.getenv("AZURE_INFERENCE_ENDPOINT")
credential = os.getenv("AZURE_INFERENCE_CREDENTIAL")

if not endpoint or not credential:
    raise ValueError("Please set AZURE_INFERENCE_ENDPOINT and AZURE_INFERENCE_CREDENTIAL environment variables")

client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(credential),
    api_version="2024-05-01-preview"
)

# Instrument the client
lilypad.instrument_azure(client)

# Non-streaming example
print("Non-streaming example:")
response = client.complete(
    messages=[
        SystemMessage(content="You are a helpful assistant."),
        UserMessage(content="Hello! How's it going?"),
    ],
    model="Ministral-3B-hgtva",  # or your deployed model name
    max_tokens=100,
    temperature=0.7,
)

if response.choices:
    print(response.choices[0].message.content)

print("\n" + "="*50 + "\n")

# Streaming example
print("Streaming example:")
stream_response = client.complete(
    messages=[
        SystemMessage(content="You are a helpful assistant."),
        UserMessage(content="Count from 1 to 5 and say goodbye."),
    ],
    model="Ministral-3B-hgtva",  # or your deployed model name
    max_tokens=100,
    temperature=0.7,
    stream=True
)

for chunk in stream_response:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()  # New line after streaming