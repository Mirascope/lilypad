from functools import lru_cache
from typing import Annotated, Any

import posthog
from fastapi import Depends, Request

from ..schemas.users import UserPublic
from ..settings import get_settings
from .auth import get_current_user


@lru_cache
def get_posthog_client() -> posthog.Posthog:
    """Get PostHog client."""
    settings = get_settings()
    return posthog.Posthog(
        api_key="",
        project_api_key=settings.posthog_api_key,
        host=settings.posthog_host,
    )


class PostHog:
    def __init__(
        self,
        request: Request,
        posthog: posthog.Posthog,
        user: UserPublic,
    ) -> None:
        """PostHog analytics class."""
        self.request = request
        self.posthog = posthog
        self.user = user

    def get_base_properties(self) -> dict[str, Any]:
        properties = {
            "path": str(self.request.url),
            "method": self.request.method,
        }
        return properties

    def capture(
        self, event_name: str, additional_properties: dict | None = None
    ) -> None:
        properties = self.get_base_properties()

        if additional_properties:
            properties.update(additional_properties)

        self.posthog.capture(
            distinct_id=self.user.email,
            event=event_name,
            properties=properties,
        )


def get_posthog(
    request: Request,
    posthog: Annotated[posthog.Posthog, Depends(get_posthog_client)],
    user: Annotated[UserPublic, Depends(get_current_user)],
) -> PostHog:
    return PostHog(request, posthog, user)
