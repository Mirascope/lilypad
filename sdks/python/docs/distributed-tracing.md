# Distributed Tracing Guide

Lilypad supports distributed tracing using OpenTelemetry context propagation, allowing you to trace requests across multiple services and processes.

## Important Note on Global State

**WARNING**: Lilypad's context propagation modifies the global OpenTelemetry propagator by calling `propagate.set_global_textmap()`. This affects all OpenTelemetry instrumentation in your process. If you have other OpenTelemetry integrations, they will use Lilypad's configured propagator.

You can control the propagator type and preserve existing propagators using the `configure()` function:

```python
import lilypad

# Use a specific propagator
lilypad.configure(
    api_key="your-api-key",
    project_id="your-project-id",
    propagator="tracecontext"  # or "b3", "b3multi", "jaeger", "composite"
)

# Preserve existing OpenTelemetry propagator
lilypad.configure(
    api_key="your-api-key",
    project_id="your-project-id",
    propagator="tracecontext",
    preserve_existing_propagator=True  # Combines with existing propagator
)
```

## Overview

Distributed tracing enables you to:
- Track requests across service boundaries
- Maintain parent-child relationships between spans in different processes
- Visualize the complete flow of a request through your system
- Debug performance issues in distributed systems

## Quick Start

### 1. Basic Setup

```python
import lilypad

# Configure Lilypad with your API credentials
lilypad.configure(
    api_key="your-api-key",
    project_id="your-project-id"
)
```

### 2. Automatic HTTP Instrumentation (Recommended)

The easiest way to enable distributed tracing is using automatic instrumentation:

```python
import lilypad

# Configure and enable automatic HTTP instrumentation
lilypad.configure(
    api_key="your-api-key",
    project_id="your-project-id",
    auto_http=True  # Enable automatic HTTP client instrumentation
)

# Now ALL HTTP calls will automatically propagate trace context!
import requests

@lilypad.trace()
def my_service():
    # This request automatically includes trace headers
    response = requests.get("https://api.example.com/data")
    return response.json()
```

You can also manually instrument specific HTTP clients after configuration:

```python
import lilypad

lilypad.configure(api_key="your-key", project_id="your-project")

# Instrument specific clients
lilypad.instrument_requests()
lilypad.instrument_httpx()
lilypad.instrument_aiohttp()
lilypad.instrument_urllib3()
```

### 3. Server-Side Context Extraction

On the receiving service, use context managers to extract trace context from incoming requests:

```python
from fastapi import FastAPI, Request
import lilypad

app = FastAPI()

# Define traced functions at module level
@lilypad.trace()
async def process_data(data: dict) -> dict:
    # This function is traced
    result = await heavy_processing(data)
    return {"status": "success", "result": result}

@app.post("/api/process")
async def process_request(request: Request, data: dict):
    # Use context manager to propagate trace context
    with lilypad.propagated_context(dict(request.headers)):
        # process_data will be a child of the upstream service's span
        # Note: Without FastAPI instrumentation, process_request itself won't be traced
        return await process_data(data)
```

> **Note**: This PR does not include automatic FastAPI instrumentation. The FastAPI endpoint (`process_request`) itself won't create a span. Only functions decorated with `@lilypad.trace()` will be traced as children of the upstream service's span.

## Complete Example: Distributed RAG System

Here's a complete example showing automatic trace propagation across services:

### Service A: Main Application

```python
# main_app.py
import lilypad

# Configure with automatic HTTP instrumentation
lilypad.configure(
    api_key="your-key",
    project_id="your-project",
    auto_http=True  # Enable automatic HTTP instrumentation
)

import requests  # Can be imported before or after configure()

# Your API client that uses requests/httpx internally
class RetrievalClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def retrieve(self, query: str, k: int) -> list:
        # Standard HTTP call - trace context added automatically!
        response = requests.post(
            f"{self.base_url}/retrieve",
            json={"query": query, "k": k}
        )
        return response.json()["documents"]

@lilypad.trace()
def rag_pipeline(query: str):
    # Initialize client
    client = RetrievalClient("http://retrieval-service:8000")
    
    # Remote call - trace propagated automatically!
    documents = client.retrieve(query, k=10)
    
    # Generate answer
    answer = generate_answer(query, documents)
    
    return {"query": query, "answer": answer}

@lilypad.trace()
def generate_answer(query: str, docs: list) -> str:
    # LLM generation logic here
    return f"Answer based on {len(docs)} documents..."
```

### Service B: Retrieval Service

```python
# retrieval_service.py
from flask import Flask, request, jsonify
import lilypad

# Configure Lilypad
lilypad.configure(
    api_key="your-key",
    project_id="your-project",
    auto_http=True  # Also enable here for outgoing calls
)

app = Flask(__name__)

# Define traced functions at module level
@lilypad.trace()
def lexical_search(query: str, k: int) -> list:
    # BM25 or similar
    return [...]

@lilypad.trace()
def semantic_search(query: str, k: int) -> list:
    # Vector search
    return [...]

@lilypad.trace()
def rerank(query: str, docs: list) -> list:
    # Re-ranking logic
    return sorted(docs, key=lambda d: d.score, reverse=True)

@lilypad.trace()
def handle_retrieve(query: str, k: int):
    # These spans are children of the caller's span
    lexical_docs = lexical_search(query, k)
    semantic_docs = semantic_search(query, k)
    ranked_docs = rerank(query, lexical_docs + semantic_docs)
    return ranked_docs[:k]

@app.route("/retrieve", methods=["POST"])
def retrieve_endpoint():
    data = request.json
    
    # Extract trace context using context manager
    with lilypad.propagated_context(dict(request.headers)):
        documents = handle_retrieve(data["query"], data["k"])
    
    return jsonify({
        "documents": [doc.to_dict() for doc in documents]
    })
```

### The Result

With automatic instrumentation, you get a complete distributed trace showing:

```
rag_pipeline()                          [Service A]
├── client.retrieve()                   [HTTP call with auto-injected headers]
│   └── handle_retrieve()               [Service B - extracted context]
│       ├── lexical_search()
│       ├── semantic_search()
│       └── rerank()
└── generate_answer()                   [Service A]
```

All trace context propagation happens automatically!

## Advanced Usage

### Manual Context Extraction

While automatic instrumentation handles context injection, you may need to manually extract context in special cases. Use Lilypad's context managers for this:

```python
# Use Lilypad's context managers for extraction
with lilypad.propagated_context(dict(request.headers)):
    # Your traced functions here will be children of the incoming trace
    process_data(data)

# Or for more control
with lilypad.context(extract_from=message["headers"]):
    # Extract context from custom message headers
    handle_message(data)
```

These context managers handle the complexity of attach/detach automatically.

### Cross-Thread Context Propagation

```python
from opentelemetry import context as otel_context
import lilypad
import threading

@lilypad.trace()
def process_in_thread(data: dict):
    # This function is defined at module level
    return transform_data(data)

@lilypad.trace()
def main_process(data: dict):
    # Capture current context
    current_ctx = otel_context.get_current()
    
    # Pass to worker thread
    thread = threading.Thread(
        target=worker_process, 
        args=(data, current_ctx)
    )
    thread.start()

def worker_process(data: dict, parent_ctx):
    # Use context manager for parent context
    with lilypad.context(parent=parent_ctx):
        # This span is a child of main_process
        return process_in_thread(data)
```

### Message Queue Integration

For message queues and other non-HTTP communication, you'll need to handle context propagation:

```python
import lilypad

# Producer - context needs to be manually included in message
@lilypad.trace()
def send_message(message: dict):
    # When using message queues, you'll need to ensure trace headers
    # are included in your message metadata. The exact mechanism
    # depends on your message queue system.
    queue.send({
        "data": message,
        # Include trace context in your message format
    })

# Consumer
@lilypad.trace()
def handle_message(data: dict):
    # Process the message
    return process(data)

def process_message(message: dict):
    # Use context manager to extract context from message headers
    with lilypad.context(extract_from=message.get("headers", {})):
        # Maintains trace context from producer
        return handle_message(message["data"])
```

Note: Automatic instrumentation currently works for HTTP clients only. For message queues, you'll need to ensure trace context is preserved in your message format.

## Configuration Options

### Propagator Types

Configure the propagation format based on your infrastructure:

```python
# W3C Trace Context (default) - Standard format
lilypad.configure(propagator="tracecontext")

# B3 Single Format - For Zipkin/Jaeger compatibility
lilypad.configure(propagator="b3")

# B3 Multi Format - Legacy B3 format
lilypad.configure(propagator="b3multi")

# Jaeger Format - For Jaeger native format
lilypad.configure(propagator="jaeger")

# Composite - Supports all formats
lilypad.configure(propagator="composite")
```

### HTTP Client Instrumentation Options

```python
# Option 1: Auto-instrument all HTTP clients
lilypad.configure(auto_http=True)

# Option 2: Selective manual instrumentation after configuration
lilypad.configure(...)
lilypad.instrument_requests()    # Just requests
lilypad.instrument_httpx()       # Just httpx (sync and async)
lilypad.instrument_aiohttp()     # Just aiohttp
lilypad.instrument_urllib3()     # Just urllib3
```

## Best Practices

1. **Use Automatic Instrumentation**: Enable `auto_http=True` in configure for transparent tracing
2. **Define Traced Functions at Module Level**: Don't define traced functions inside request handlers
3. **Consistent Propagation**: Use the same propagation format across all services
4. **Use Context Managers**: Use `propagated_context()` and `context()` for manual context management
5. **Rely on Automatic Instrumentation**: Let Lilypad handle context propagation automatically
6. **Performance**: Context propagation adds minimal overhead (typically < 1ms)

## Troubleshooting

### Traces Not Connecting

1. Verify automatic instrumentation is enabled on both services:
   ```python
   lilypad.configure(auto_http=True)
   ```

2. Check that trace context headers are being passed:
   - Look for `traceparent` header (W3C)
   - Look for `b3` or `x-b3-*` headers (B3)
   - Look for `uber-trace-id` header (Jaeger)

3. Ensure both services are configured with the same Lilypad project

4. Verify the same propagation format is used across services

### Missing Spans

1. Ensure functions are decorated with `@lilypad.trace()`
2. For server handlers, use context managers to extract context
3. Check that Lilypad is configured before making traced calls

### Automatic Instrumentation Not Working

Some scenarios where automatic instrumentation might not work:

1. **Custom HTTP Clients**: Libraries that don't use standard HTTP clients internally
2. **Subclassed Clients**: Custom subclasses of HTTP clients may not be instrumented

In these cases, automatic instrumentation may not work. Consider:
1. Using a supported HTTP client (requests, httpx, aiohttp, urllib3)
2. Wrapping your custom client with a supported HTTP client

Note: As of the latest version, import order no longer matters! HTTP libraries can be imported before or after `lilypad.configure()`:
```python
# Both of these work now:

# Option 1: Import before configure
import requests
lilypad.configure(auto_http=True)

# Option 2: Import after configure
lilypad.configure(auto_http=True)
import requests
```

## Environment Variables

- `LILYPAD_PROPAGATOR`: Set default propagation format (can be overridden in configure())

## Future Roadmap

### FastAPI Instrumentation (Coming Soon)

Native FastAPI instrumentation is planned for a future release. This will provide automatic context extraction and span creation for FastAPI applications:

```python
# Future API (not yet available)
import lilypad
from fastapi import FastAPI

app = FastAPI()
lilypad.instrument_fastapi(app)

# This will automatically:
# - Extract trace context from incoming requests
# - Create spans for each endpoint
# - Propagate context to traced functions
@app.post("/api/process")
async def process_request(data: dict):
    # Automatically wrapped in proper trace context
    return await process_data(data)
```

Until this feature is available, use the `propagated_context()` context manager as shown in the examples above.

## Example: Complete RAG System

See the [examples directory](../examples/) for complete examples of distributed RAG systems with automatic trace propagation.