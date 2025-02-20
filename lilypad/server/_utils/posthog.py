import time
from collections.abc import Awaitable, Callable
from functools import lru_cache
from typing import Any

import posthog
from fastapi import Request, Response
from fastapi.applications import FastAPI
from fastapi.routing import APIRoute

from ..settings import get_settings


@lru_cache
def get_posthog_client() -> posthog.Posthog:
    """Get PostHog client."""
    settings = get_settings()
    return posthog.Posthog(
        api_key="",
        project_api_key=settings.posthog_api_key,
        host=settings.posthog_host,
    )


class PosthogMiddleware:
    def __init__(
        self,
        exclude_paths: list[str] | None = None,
        should_capture: Callable[[Request], bool] | None = None,
    ) -> None:
        """Initialize the PostHog middleware.

        Args:
            settings: Application settings
            exclude_paths: List of paths to exclude from tracking
            should_capture: Optional function that takes a request and returns
                          whether the event should be captured
        """
        self.posthog = get_posthog_client()
        self.exclude_paths = exclude_paths or []
        self.should_capture = should_capture or (lambda _: True)

    def get_base_properties(self, request: Request) -> dict[str, Any]:
        """Get base properties for PostHog events."""
        return {
            "path": str(request.url),
            "method": request.method,
            "user_agent": request.headers.get("user-agent"),
            "referer": request.headers.get("referer"),
        }

    async def __call__(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Skip if path is excluded
        path = request.url.path
        if path in self.exclude_paths:
            return await call_next(request)

        # Skip if should_capture returns False
        if not self.should_capture(request):
            return await call_next(request)

        # Capture request start time
        start_time = time.time()

        # Process the request
        response = await call_next(request)

        # Calculate request duration
        duration = time.time() - start_time

        try:
            # Try to get authenticated user from request state
            user = request.state.user
            distinct_id = user.email if user else "anonymous"
        except AttributeError:
            distinct_id = "anonymous"

        # Get the route and function name
        route = request.scope.get("route")
        event_name = (
            route.endpoint.__name__ if isinstance(route, APIRoute) else "api_request"
        )

        # Get base properties
        properties = self.get_base_properties(request)

        # Add response properties
        properties.update(
            {
                "status_code": response.status_code,
                "duration": duration,
            }
        )

        # Capture the event
        self.posthog.capture(
            distinct_id=distinct_id,
            event=event_name,
            properties=properties,
        )

        return response


def setup_posthog_middleware(
    app: FastAPI,
    exclude_paths: list[str] | None = None,
    should_capture: Callable[[Request], bool] | None = None,
) -> None:
    """Setup PostHog middleware for a FastAPI application.

    Args:
        app: FastAPI application instance
        settings: Application settings containing PostHog configuration
        exclude_paths: List of paths to exclude from tracking
        should_capture: Optional function that takes a request and returns
                       whether the event should be captured

    Example:
        ```python
        from fastapi import FastAPI

        app = FastAPI()
        settings = get_settings()  # Your settings function

        # Exclude health check and metrics endpoints
        exclude_paths = ["/health", "/metrics"]

        setup_posthog_middleware(
            app,
            settings,
            exclude_paths=exclude_paths
        )
        ```
    """
    middleware = PosthogMiddleware(
        exclude_paths=exclude_paths, should_capture=should_capture
    )
    app.middleware("http")(middleware)
