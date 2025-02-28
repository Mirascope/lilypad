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
        disabled=settings.environment != "production",
    )


class PosthogMiddleware:
    def __init__(
        self,
        exclude_paths: list[str],
        should_capture: Callable[[Request], bool],
    ) -> None:
        """Initialize the PostHog middleware.

        Args:
            settings: Application settings
            exclude_paths: List of paths to exclude from tracking
            should_capture: Optional function that takes a request and returns
                          whether the event should be captured
        """
        self.posthog = get_posthog_client()
        self.exclude_paths = exclude_paths
        self.should_capture = should_capture

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
        path = request.url.path
        if path in self.exclude_paths:
            return await call_next(request)

        if not self.should_capture(request) or request.method in ["OPTIONS", "GET"]:
            return await call_next(request)

        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time
        try:
            user = request.state.user
            distinct_id = user.email if user else "anonymous"
        except AttributeError:
            distinct_id = "anonymous"

        route = request.scope.get("route")
        event_name = (
            route.endpoint.__name__ if isinstance(route, APIRoute) else "api_request"
        )

        properties = self.get_base_properties(request)

        properties.update(
            {
                "status_code": response.status_code,
                "duration": duration,
            }
        )

        self.posthog.capture(
            distinct_id=distinct_id,
            event=event_name,
            properties=properties,
        )

        return response


def setup_posthog_middleware(
    app: FastAPI,
    exclude_paths: list[str],
    should_capture: Callable[[Request], bool],
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

        # Exclude health check and metrics endpoints
        exclude_paths = ["/health", "/metrics"]

        setup_posthog_middleware(
            app,
            exclude_paths=exclude_paths
        )
        ```
    """
    middleware = PosthogMiddleware(
        exclude_paths=exclude_paths, should_capture=should_capture
    )
    app.middleware("http")(middleware)
