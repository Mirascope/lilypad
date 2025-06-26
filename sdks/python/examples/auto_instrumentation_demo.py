"""Simple demonstration of automatic HTTP client instrumentation.

This example shows how trace context is automatically propagated without any code changes.
"""

from typing import List, Any
import lilypad
import requests
import requests.adapters

# Configure Lilypad with auto-instrumentation
lilypad.configure(
    # api_key="your-api-key",
    # project_id="your-project-id",
    auto_http=True  # Enable auto-instrumentation for HTTP libraries
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

    def capture_request(self, request: requests.PreparedRequest) -> None:
        """Capture headers from a request."""
        for key, value in request.headers.items():
            if key.lower() in ["traceparent", "b3", "uber-trace-id"]:
                self.captured_headers[key] = value


# Patch requests to show headers
header_capture = HeaderCapture()
original_send = requests.adapters.HTTPAdapter.send


def patched_send(
    self: requests.adapters.HTTPAdapter, request: requests.PreparedRequest, **kwargs: Any
) -> requests.Response:
    header_capture.capture_request(request)
    # Create mock response
    from requests.models import Response

    resp = Response()
    resp.status_code = 200
    resp._content = b'{"documents": [{"id": "1", "content": "test", "score": 0.9}]}'
    resp.headers["Content-Type"] = "application/json"
    return resp


requests.adapters.HTTPAdapter.send = patched_send  # pyright: ignore [reportAttributeAccessIssue]


# Example 1: Simple traced function making HTTP call
@lilypad.trace()
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
        response = requests.post(f"{self.base_url}/search", json={"query": query, "k": k})
        data = response.json()
        return [Document(**doc) for doc in data.get("documents", [])]


@lilypad.trace()
def rag_pipeline(query: str) -> dict:
    """RAG pipeline using RPC client - trace propagates automatically."""
    # Create client
    client = APIClient("http://api.example.com")

    # This call automatically includes trace headers!
    documents = client.remote_search(query, k=5)

    # Generate answer
    answer = f"Found {len(documents)} documents for '{query}'"

    return {"query": query, "answer": answer, "documents": [doc.id for doc in documents]}


# Example 3: Service-to-service communication
@lilypad.trace()
def microservice_a(data: dict) -> dict:
    """Service A calls Service B - trace context flows automatically."""

    # Call another service - trace headers added automatically
    response = requests.post("http://service-b.example.com/process", json=data)

    return response.json()


def main() -> None:
    # Example 1: Simple GET request
    result = fetch_data("http://api.example.com/data")

    # Example 2: RPC Client
    rag_result = rag_pipeline("What is distributed tracing?")

    # Example 3: Microservices
    service_result = microservice_a({"action": "process", "data": "important"})

    # Summary


if __name__ == "__main__":
    main()
