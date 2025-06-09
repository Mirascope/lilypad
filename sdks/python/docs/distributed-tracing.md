# Distributed Tracing Guide

Lilypad supports distributed tracing using OpenTelemetry context propagation, allowing you to trace requests across multiple services and processes.

## Important Note on Global State

**WARNING**: Lilypad's context propagation modifies the global OpenTelemetry propagator by calling `propagate.set_global_textmap()`. This affects all OpenTelemetry instrumentation in your process. If you have other OpenTelemetry integrations, they will use Lilypad's configured propagator.

You can control the propagator type via the `LILYPAD_PROPAGATOR` environment variable:
- `tracecontext` (default): W3C Trace Context
- `b3`: B3 Single Format
- `b3multi`: B3 Multi Format
- `jaeger`: Jaeger format
- `composite`: All formats for maximum compatibility

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

### 2. Automatic Instrumentation (Recommended)

The easiest way to enable distributed tracing is using automatic instrumentation:

```python
from lilypad.integrations import instrument_http_clients

# Enable at application startup
instrument_http_clients()

# Now ALL HTTP calls will automatically propagate trace context!
import requests

@lilypad.trace()
def my_service():
    # This request automatically includes trace headers
    response = requests.get("https://api.example.com/data")
    return response.json()
```

This approach works with any HTTP-based RPC client that uses standard libraries internally:

```python
# Enable auto-instrumentation once
instrument_http_clients()

# Your RPC client (gRPC, JSON-RPC, custom client, etc.)
from my_api import Client

@lilypad.trace()
def rag(query: str):
    client = Client("https://api.example.com")
    # The underlying HTTP calls automatically include trace context!
    docs = client.retrieve(query, k=5)
    return generate_answer(query, docs)
```

### 3. Server-Side Context Extraction

On the receiving service, extract trace context from incoming requests:

```python
from fastapi import FastAPI, Request
from lilypad import trace

app = FastAPI()

@app.post("/api/process")
async def process_request(request: Request, data: dict):
    # Extract trace context from HTTP headers
    @trace(extract_from=dict(request.headers))
    async def process_data(data: dict) -> dict:
        # This span will be a child of the caller's span
        result = await heavy_processing(data)
        return {"status": "success", "result": result}
    
    return await process_data(data)
```

## Complete Example: Distributed RAG System

Here's a complete example showing automatic trace propagation across services:

### Service A: Main Application

```python
# main_app.py
from lilypad import trace, configure
from lilypad.integrations import instrument_http_clients

# Enable automatic instrumentation
instrument_http_clients()

# Configure Lilypad
configure(api_key="your-key", project_id="your-project")

# Your API client that uses requests/httpx internally
class RetrievalClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def retrieve(self, query: str, k: int) -> list:
        # Standard HTTP call - trace context added automatically!
        import requests
        response = requests.post(
            f"{self.base_url}/retrieve",
            json={"query": query, "k": k}
        )
        return response.json()["documents"]

@trace()
def rag_pipeline(query: str):
    # Initialize client
    client = RetrievalClient("http://retrieval-service:8000")
    
    # Remote call - trace propagated automatically!
    documents = client.retrieve(query, k=10)
    
    # Generate answer
    answer = generate_answer(query, documents)
    
    return {"query": query, "answer": answer}

@trace()
def generate_answer(query: str, docs: list) -> str:
    # LLM generation logic here
    return f"Answer based on {len(docs)} documents..."
```

### Service B: Retrieval Service

```python
# retrieval_service.py
from flask import Flask, request, jsonify
from lilypad import trace, configure
from lilypad.integrations import instrument_http_clients

# Enable automatic instrumentation for outgoing calls
instrument_http_clients()

# Configure Lilypad
configure(api_key="your-key", project_id="your-project")

app = Flask(__name__)

@app.route("/retrieve", methods=["POST"])
def retrieve_endpoint():
    data = request.json
    
    # Extract trace context from incoming headers
    @trace(extract_from=dict(request.headers))
    def handle_retrieve(query: str, k: int):
        # These spans are children of the caller's span
        lexical_docs = lexical_search(query, k)
        semantic_docs = semantic_search(query, k)
        ranked_docs = rerank(query, lexical_docs + semantic_docs)
        return ranked_docs[:k]
    
    documents = handle_retrieve(data["query"], data["k"])
    
    return jsonify({
        "documents": [doc.to_dict() for doc in documents]
    })

@trace()
def lexical_search(query: str, k: int) -> list:
    # BM25 or similar
    return [...]

@trace()
def semantic_search(query: str, k: int) -> list:
    # Vector search
    return [...]

@trace()
def rerank(query: str, docs: list) -> list:
    # Re-ranking logic
    return sorted(docs, key=lambda d: d.score, reverse=True)
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

## Manual HTTP Client Integration

If you prefer explicit control or automatic instrumentation doesn't work for your use case:

### Using Traced HTTP Clients

```python
# Using pre-built traced clients
from lilypad.integrations.http_client import TracedRequestsSession

@trace()
def fetch_data():
    with TracedRequestsSession() as session:
        # Trace context automatically added
        response = session.get("https://api.example.com/data")
        return response.json()
```

### Manual Context Injection

```python
from lilypad._utils.context_propagation import inject_context
import httpx

@trace()
async def manual_propagation():
    headers = {}
    # Manually inject trace context
    inject_context(headers)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.example.com/data",
            headers=headers
        )
        return response.json()
```

## Advanced Usage

### Cross-Thread Context Propagation

```python
from opentelemetry import context as otel_context
import threading

@trace()
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
    @trace(parent_context=parent_ctx)
    def process_in_thread(data: dict):
        # This span is a child of main_process
        return transform_data(data)
    
    return process_in_thread(data)
```

### Message Queue Integration

```python
# Producer
@trace()
def send_message(message: dict):
    headers = {}
    inject_context(headers)
    
    # Include headers in message metadata
    queue.send({
        "data": message,
        "headers": headers
    })

# Consumer
def process_message(message: dict):
    @trace(extract_from=message["headers"])
    def handle_message(data: dict):
        # Maintains trace context from producer
        return process(data)
    
    return handle_message(message["data"])
```

## Environment Variables

- `LILYPAD_PROPAGATOR`: Set propagation format (tracecontext, b3, jaeger, composite)
- `LILYPAD_HTTP_CLIENT`: Preferred HTTP client for `get_traced_http_client()` (requests, httpx, aiohttp)

## Best Practices

1. **Use Automatic Instrumentation**: Call `instrument_http_clients()` once at startup for transparent tracing
2. **Consistent Propagation**: Use the same propagation format across all services
3. **Extract at Service Boundaries**: Always extract context from incoming requests in server handlers
4. **Error Handling**: Both automatic and manual approaches handle propagation errors gracefully
5. **Performance**: Context propagation adds minimal overhead (typically < 1ms)

## Troubleshooting

### Traces Not Connecting

1. Verify automatic instrumentation is enabled on both services
2. Check that trace context headers are being passed (look for `traceparent` header)
3. Ensure both services are configured with the same Lilypad project
4. Verify the same propagation format is used across services

### Missing Spans

1. Verify the @trace decorator is applied to all relevant functions
2. For server handlers, ensure you're extracting context with `extract_from`
3. Check that Lilypad is configured before making traced calls

### Automatic Instrumentation Not Working

1. Ensure `instrument_http_clients()` is called before importing HTTP libraries
2. Some custom HTTP clients may not use standard libraries internally
3. Fall back to manual traced clients or context injection if needed

## Example: Complete RAG System

See the [auto instrumentation example](../examples/auto_instrumentation_example.py) for a complete example of a distributed RAG system with automatic trace propagation.