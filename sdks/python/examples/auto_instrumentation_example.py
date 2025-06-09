"""Example demonstrating automatic distributed tracing without explicit traced clients.

This example shows how to achieve transparent distributed tracing across service
boundaries, matching the original vision where trace context is automatically
propagated without code changes.
"""

import asyncio
from typing import List
import requests

# Enable automatic instrumentation at the start
from lilypad.integrations import instrument_http_clients
from lilypad import trace, configure

# Enable automatic trace propagation for ALL HTTP calls
instrument_http_clients()

# Configure Lilypad
configure(
    api_key="your-api-key",
    project_id="your-project-id"
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
@trace()
def lexical_retr(query: str, k: int) -> List[Document]:
    """Lexical retrieval using BM25 or similar."""
    # Simulate lexical search
    return [Document(f"lex_{i}", f"Lexical result {i} for: {query}") for i in range(k)]


@trace()
def semantic_retr(query: str, k: int) -> List[Document]:
    """Semantic retrieval using embeddings."""
    # Simulate semantic search
    return [Document(f"sem_{i}", f"Semantic result {i} for: {query}") for i in range(k)]


@trace()
def rerank(query: str, docs: List[Document]) -> List[Document]:
    """Rerank documents by relevance."""
    # Simulate reranking
    for i, doc in enumerate(docs):
        doc.score = 1.0 / (i + 1)
    return sorted(docs, key=lambda d: d.score, reverse=True)


@trace()
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
        response = requests.post(
            f"{self.base_url}/retrieve",
            json={"query": query, "k": k}
        )
        response.raise_for_status()
        
        # Convert response back to Document objects
        data = response.json()
        return [
            Document(doc["id"], doc["content"], doc["score"]) 
            for doc in data["documents"]
        ]


# This is on the caller process
@trace()
def generate(query: str, docs: List[Document]) -> str:
    """Generate answer based on retrieved documents."""
    context = "\n".join(doc.content for doc in docs)
    return f"Based on the search for '{query}', here's what I found: {context[:200]}..."


@trace()
def rag(query: str):
    """RAG pipeline that makes remote calls.
    
    This demonstrates the key feature: the remote call to client.retr()
    will automatically propagate trace context because we enabled
    auto-instrumentation. No manual header injection needed!
    """
    # Initialize client (could be any RPC client using HTTP)
    client = RetrievalClient("http://retrieval-service:8000")
    
    # This remote call automatically includes trace headers!
    # The trace will show the full distributed call stack
    docs = client.retr(query, 5)
    
    # Generate answer based on retrieved docs
    answer = generate(query, docs)
    
    return {
        "query": query,
        "answer": answer,
        "sources": [doc.id for doc in docs]
    }


# Example with popular RPC libraries
class GRPCExample:
    """Example showing how gRPC clients would also work automatically."""
    
    @trace()
    def call_grpc_service(self, request):
        # If the gRPC client uses requests/httpx internally,
        # trace context is automatically propagated!
        import grpc
        
        # This would automatically include trace headers
        # if gRPC uses instrumented HTTP libraries
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = MyServiceStub(channel)
            response = stub.MyMethod(request)
            return response


# Example with async clients
@trace()
async def async_rag(query: str):
    """Async version using httpx (also automatically instrumented)."""
    import httpx
    
    # Even async httpx is automatically instrumented!
    async with httpx.AsyncClient() as client:
        # Trace context is automatically added to this request
        response = await client.post(
            "http://retrieval-service:8000/retrieve",
            json={"query": query, "k": 5}
        )
        data = response.json()
    
    # Process the results
    answer = await async_generate(query, data["documents"])
    return {"query": query, "answer": answer}


@trace()
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


@app.post("/retrieve")
async def retrieve_endpoint(request: Request, data: RetrieveRequest):
    """Server endpoint that extracts trace context from headers."""
    
    # Extract trace context from incoming headers
    @trace(extract_from=dict(request.headers))
    def handle_retrieve():
        # This span is automatically a child of the caller's span!
        return retr(data.query, data.k)
    
    docs = handle_retrieve()
    
    return {
        "documents": [
            {"id": doc.id, "content": doc.content, "score": doc.score}
            for doc in docs
        ]
    }


def main():
    """Demonstrate the automatic distributed tracing."""
    
    print("=== Automatic Distributed Tracing Example ===\n")
    
    # The key insight: We only need to call this once at startup!
    print("1. Auto-instrumentation enabled at import time")
    print("   All HTTP calls now automatically propagate trace context!\n")
    
    # Example 1: Synchronous RAG pipeline
    print("2. Running synchronous RAG pipeline...")
    result = rag("who is the king of england?")
    print(f"   Query: {result['query']}")
    print(f"   Answer: {result['answer'][:100]}...")
    print(f"   Sources: {result['sources']}\n")
    
    # Example 2: Async pipeline
    print("3. Running async RAG pipeline...")
    async_result = asyncio.run(async_rag("what is quantum computing?"))
    print(f"   Query: {async_result['query']}")
    print(f"   Answer: {async_result['answer']}\n")
    
    print("=== Key Benefits ===")
    print("- No need to modify existing HTTP client code")
    print("- Works with any HTTP-based RPC library")
    print("- Trace context flows automatically across services")
    print("- Single trace ID across entire distributed call")
    print("\nThe trace shows the complete call hierarchy:")
    print("  rag()")
    print("    └── client.retr()  [remote call with auto-injected headers]")
    print("         └── retr()  [on retrieval server]") 
    print("              ├── lexical_retr()")
    print("              ├── semantic_retr()")
    print("              └── rerank()")
    print("    └── generate()")


if __name__ == "__main__":
    # To run the server:
    # python auto_instrumentation_example.py --server
    
    import sys
    if "--server" in sys.argv:
        print("Starting retrieval server on port 8000...")
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        main()