"""Example demonstrating automatic distributed tracing without explicit traced clients.

This example shows how to achieve transparent distributed tracing across service
boundaries, matching the original vision where trace context is automatically
propagated without code changes.
"""

import asyncio
from typing import List, Any

import lilypad
import requests

# Configure Lilypad with automatic HTTP instrumentation
lilypad.configure(
    # api_key="your-api-key",
    # project_id="your-project-id",
    auto_http=True  # Enable automatic trace propagation for ALL HTTP calls
)


# Example: Document retrieval service (runs on separate server)
class Document:
    def __init__(self, id: str, content: str, score: float = 0.0):
        self.id = id
        self.content = content
        self.score = score

    def __repr__(self):
        return f"Document(id={self.id}, score={self.score})"


# This would be on the retrieval server
@lilypad.trace()
def lexical_retr(query: str, k: int) -> List[Document]:
    """Lexical retrieval using BM25 or similar."""
    # Simulate lexical search
    return [Document(f"lex_{i}", f"Lexical result {i} for: {query}") for i in range(k)]


@lilypad.trace()
def semantic_retr(query: str, k: int) -> List[Document]:
    """Semantic retrieval using embeddings."""
    # Simulate semantic search
    return [Document(f"sem_{i}", f"Semantic result {i} for: {query}") for i in range(k)]


@lilypad.trace()
def rerank(query: str, docs: List[Document]) -> List[Document]:
    """Rerank documents by relevance."""
    # Simulate reranking
    for i, doc in enumerate(docs):
        doc.score = 1.0 / (i + 1)
    return sorted(docs, key=lambda d: d.score, reverse=True)


@lilypad.trace()
def retr(query: str, k: int) -> List[Document]:
    """Main retrieval function that orchestrates the retrieval pipeline."""
    lexdocs = lexical_retr(query, k)
    semdocs = semantic_retr(query, k)
    ranked = rerank(query, lexdocs + semdocs)
    return ranked[:k]


# Simulated RPC client that uses requests internally
class RetrievalClient:
    """A client that makes HTTP calls to the retrieval service.

    This simulates any RPC client (gRPC, JSON-RPC, custom HTTP client, etc.)
    that uses standard HTTP libraries internally.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url

    def retr(self, query: str, k: int) -> List[Document]:
        """Make a remote call to the retrieval service.

        Because we called instrument_http_clients(), this request
        will AUTOMATICALLY include trace context headers!
        """
        # This is just using standard requests - no special tracing code!
        response = requests.post(f"{self.base_url}/retrieve", json={"query": query, "k": k})
        response.raise_for_status()

        # Convert response back to Document objects
        data = response.json()
        return [Document(doc["id"], doc["content"], doc["score"]) for doc in data["documents"]]


# This is on the caller process
@lilypad.trace()
def generate(query: str, docs: List[Document]) -> str:
    """Generate answer based on retrieved documents."""
    context = "\n".join(doc.content for doc in docs)
    return f"Based on the search for '{query}', here's what I found: {context[:200]}..."


@lilypad.trace()
def rag(query: str) -> dict[str, Any]:
    """RAG pipeline that makes remote calls.

    This demonstrates the key feature: the remote call to client.retr()
    will automatically propagate trace context because we enabled
    auto-instrumentation. No manual header injection needed!
    """
    # Initialize client (could be any RPC client using HTTP)
    client = RetrievalClient("http://localhost:8000")

    # This remote call automatically includes trace headers!
    # The trace will show the full distributed call stack
    docs = client.retr(query, 5)

    # Generate answer based on retrieved docs
    answer = generate(query, docs)

    return {"query": query, "answer": answer, "sources": [doc.id for doc in docs]}


# Example showing RPC libraries that use HTTP internally
class HTTPBasedRPCExample:
    """Example showing how HTTP-based RPC clients work automatically."""

    @lilypad.trace()
    def call_json_rpc_service(self, method: str, params: dict) -> Any:
        # JSON-RPC clients that use requests/httpx internally
        # will automatically propagate trace context!

        # Example: Many JSON-RPC libraries use requests internally
        response = requests.post(
            "http://localhost:8080/jsonrpc", json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        )
        return response.json()["result"]


# Example with async clients
@lilypad.trace()
async def async_rag(query: str) -> dict[str, Any]:
    """Async version using httpx (also automatically instrumented)."""
    import httpx

    # Even async httpx is automatically instrumented!
    async with httpx.AsyncClient() as client:
        # Trace context is automatically added to this request
        response = await client.post("http://localhost:8000/retrieve", json={"query": query, "k": 5})
        data = response.json()

    # Process the results
    answer = await async_generate(query, data["documents"])
    return {"query": query, "answer": answer}


@lilypad.trace()
async def async_generate(query: str, docs: list) -> str:
    """Async document generation."""
    await asyncio.sleep(0.1)  # Simulate async work
    return f"Async answer for '{query}' based on {len(docs)} documents"


# Server-side example showing how to extract context
from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()


class RetrieveRequest(BaseModel):
    query: str
    k: int


# Define the handler function at module level
@lilypad.trace()
def handle_retrieve(query: str, k: int) -> List[Document]:
    # This span is automatically a child of the caller's span!
    return retr(query, k)


@app.post("/retrieve")
async def retrieve_endpoint(request: Request, data: RetrieveRequest) -> dict[str, list[dict[str, Any]]]:
    """Server endpoint that extracts trace context from headers."""

    # Use context manager to extract trace context from incoming headers
    with lilypad.propagated_context(extract_from=dict(request.headers)):
        docs = handle_retrieve(data.query, data.k)

    return {"documents": [{"id": doc.id, "content": doc.content, "score": doc.score} for doc in docs]}


def main() -> None:
    """Demonstrate the automatic distributed tracing."""

    # The key insight: We only need to call this once at startup!

    # Mock the HTTP calls to avoid network errors
    from unittest.mock import patch, Mock

    # Create mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "documents": [
            {"id": "doc1", "content": "The current monarch is King Charles III", "score": 0.95},
            {"id": "doc2", "content": "Charles became king in 2022", "score": 0.87},
            {"id": "doc3", "content": "The British monarchy has a long history", "score": 0.72},
            {"id": "doc4", "content": "Elizabeth II was the previous monarch", "score": 0.68},
            {"id": "doc5", "content": "The United Kingdom is a constitutional monarchy", "score": 0.64},
        ]
    }

    captured_headers = {}

    # Store original to use after patching
    original_post = requests.post

    def capture_headers(url: str, **kwargs: Any) -> Mock:
        """Capture headers to show trace propagation."""
        headers = kwargs.get("headers", {})
        if headers:
            captured_headers.update(headers)
        # Call the patched version which has auto-instrumentation
        return mock_response

    with patch("requests.post", side_effect=capture_headers):
        # Example 1: Synchronous RAG pipeline
        result = rag("who is the king of england?")

        # Show the trace headers that were sent
        for key, _value in captured_headers.items():
            if key.lower() in ["traceparent", "b3", "uber-trace-id"]:
                pass

    # Mock async response
    async_mock_response = Mock()
    async_mock_response.status_code = 200
    async_mock_response.json.return_value = {
        "documents": [
            {"id": "doc1", "content": "Quantum computing uses quantum mechanics", "score": 0.92},
            {"id": "doc2", "content": "Qubits are the basic unit of quantum information", "score": 0.85},
        ]
    }

    with patch("httpx.AsyncClient.post", return_value=async_mock_response):
        # Example 2: Async pipeline
        async_result = asyncio.run(async_rag("what is quantum computing?"))


if __name__ == "__main__":
    # To run the server:
    # python auto_instrumentation_example.py --server

    import sys

    if "--server" in sys.argv:
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        main()
