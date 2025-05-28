"""FastAPI test application for testing the API endpoints."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lilypad.server.api import v0_api


def create_mock_app() -> FastAPI:
    """Create a FastAPI test application without static file mounting."""
    app = FastAPI()

    # Add CORS middleware for testing
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://test"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount the API routes
    app.mount("/v0", v0_api)

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok"}

    return app


# Create a single instance of the test app
mock_app = create_mock_app()
