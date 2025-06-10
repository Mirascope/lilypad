"""Simple demonstration of automatic HTTP client instrumentation.

This example shows how trace context is automatically propagated without any code changes.
"""

# Enable auto-instrumentation BEFORE importing HTTP libraries
from lilypad.integrations import instrument_http_clients
instrument_http_clients()

# Now import the rest
import asyncio
from typing import List
import requests
import httpx
from lilypad import trace, configure

# Configure Lilypad
configure(
    # api_key="your-api-key",
    # project_id="your-project-id"
)


class Document:
    def __init__(self, id: str, content: str, score: float = 0.0):
        self.id = id
        self.content = content
        self.score = score


# Intercept HTTP calls to show headers
class HeaderCapture:
    """Helper to capture and display headers from HTTP requests."""
    
    def __init__(self):
        self.captured_headers = {}
        
    def capture_request(self, request):
        """Capture headers from a request."""
        print(f"\n📡 HTTP Request to: {request.url}")
        print("   Headers:")
        for key, value in request.headers.items():
            if key.lower() in ['traceparent', 'b3', 'uber-trace-id']:
                print(f"   ✅ {key}: {value}")
                self.captured_headers[key] = value


# Patch requests to show headers
header_capture = HeaderCapture()
original_send = requests.adapters.HTTPAdapter.send

def patched_send(self, request, **kwargs):
    header_capture.capture_request(request)
    # Create mock response
    from requests.models import Response
    resp = Response()
    resp.status_code = 200
    resp._content = b'{"documents": [{"id": "1", "content": "test", "score": 0.9}]}'
    resp.headers['Content-Type'] = 'application/json'
    return resp

requests.adapters.HTTPAdapter.send = patched_send


# Example 1: Simple traced function making HTTP call
@trace()
def fetch_data(url: str) -> dict:
    """Make a simple HTTP request - trace context is added automatically!"""
    # Just a normal requests call - no special tracing code!
    response = requests.get(url)
    return response.json()


# Example 2: RPC client that uses requests internally
class APIClient:
    """Simulates any RPC client that uses HTTP internally."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def remote_search(self, query: str, k: int) -> List[Document]:
        """Makes HTTP call internally - gets auto-instrumented!"""
        # Standard requests call - trace context added automatically
        response = requests.post(
            f"{self.base_url}/search",
            json={"query": query, "k": k}
        )
        data = response.json()
        return [Document(**doc) for doc in data.get("documents", [])]


@trace()
def rag_pipeline(query: str) -> dict:
    """RAG pipeline using RPC client - trace propagates automatically."""
    # Create client
    client = APIClient("http://api.example.com")
    
    # This call automatically includes trace headers!
    documents = client.remote_search(query, k=5)
    
    # Generate answer
    answer = f"Found {len(documents)} documents for '{query}'"
    
    return {
        "query": query,
        "answer": answer,
        "documents": [doc.id for doc in documents]
    }


# Example 3: Service-to-service communication
@trace()
def microservice_a(data: dict) -> dict:
    """Service A calls Service B - trace context flows automatically."""
    print("\n🔹 Service A processing...")
    
    # Call another service - trace headers added automatically
    response = requests.post(
        "http://service-b.example.com/process",
        json=data
    )
    
    return response.json()


def main():
    print("=" * 70)
    print("Automatic HTTP Client Instrumentation Demo")
    print("=" * 70)
    print("\n✨ Auto-instrumentation is enabled!")
    print("   All HTTP calls will automatically include trace context headers.\n")
    
    # Example 1: Simple GET request
    print("Example 1: Simple GET Request")
    print("-" * 40)
    result = fetch_data("http://api.example.com/data")
    print(f"   Result: {result}")
    
    # Example 2: RPC Client
    print("\n\nExample 2: RPC Client (RAG Pipeline)")
    print("-" * 40)
    rag_result = rag_pipeline("What is distributed tracing?")
    print(f"   Query: {rag_result['query']}")
    print(f"   Answer: {rag_result['answer']}")
    print(f"   Documents: {rag_result['documents']}")
    
    # Example 3: Microservices
    print("\n\nExample 3: Microservice Communication")
    print("-" * 40)
    service_result = microservice_a({"action": "process", "data": "important"})
    print(f"   Result: {service_result}")
    
    # Summary
    print("\n\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print("\n✅ All HTTP requests included trace context headers automatically!")
    print(f"✅ Captured headers: {list(header_capture.captured_headers.keys())}")
    print("\n🎯 Key Points:")
    print("   1. Call instrument_http_clients() once at startup")
    print("   2. No changes needed to HTTP client code")
    print("   3. Works with any library using requests/httpx/aiohttp")
    print("   4. Trace context flows across all service boundaries")
    print("\n📚 This enables distributed tracing without modifying existing code!")


if __name__ == "__main__":
    main()