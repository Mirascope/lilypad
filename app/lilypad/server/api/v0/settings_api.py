"""The `/settings` API router."""

import asyncio
import logging
from typing import Annotated

import httpx
from cachetools import TTLCache
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ...settings import Settings, get_settings

settings_router = APIRouter()

policy_cache = TTLCache(maxsize=1, ttl=3600)
cache_lock = asyncio.Lock()

logger = logging.getLogger(__name__)


class PolicyData(BaseModel):
    """Model for policy data from Mirascope API."""

    type: str
    path: str
    route: str
    title: str
    description: str
    slug: str
    lastUpdated: str


DEFAULT_POLICY_VERSIONS: dict[str, str | None] = {
    "privacyVersion": None,
    "termsVersion": None,
}


async def fetch_policy_versions() -> dict[str, str | None]:
    """Fetch privacy and terms version information from Mirascope API with caching."""
    cache_key = "policy_versions"

    # Check cache first
    if cache_key in policy_cache:
        return policy_cache[cache_key]

    async with cache_lock:
        # Double-check cache after acquiring lock
        if cache_key in policy_cache:
            return policy_cache[cache_key]

        url = "https://mirascope.com/static/content-meta/policy/index.json"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()

                policy_data = [PolicyData(**item) for item in response.json()]

                # Find the privacy policy and terms of service entries
                privacy_policy = next(
                    (policy for policy in policy_data if policy.slug == "privacy"), None
                )
                terms_of_service = next(
                    (policy for policy in policy_data if policy.slug == "service"), None
                )

                if not privacy_policy or not terms_of_service:
                    raise ValueError("Could not find required policy information")

                result: dict[str, str | None] = {
                    "privacyVersion": privacy_policy.lastUpdated,
                    "termsVersion": terms_of_service.lastUpdated,
                }

                # Cache the result
                policy_cache[cache_key] = result
                return result

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching policy versions: {e}")
                return DEFAULT_POLICY_VERSIONS
            except Exception as e:
                logger.error(f"Error fetching policy versions: {e}")
                return DEFAULT_POLICY_VERSIONS


class SettingsPublic(BaseModel):
    """Public settings model for client-side access."""

    remote_client_url: str
    remote_api_url: str
    github_client_id: str
    google_client_id: str
    environment: str
    experimental: bool
    privacy_version: str | None
    terms_version: str | None


@settings_router.get("/settings", response_model=SettingsPublic)
async def get_settings_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> SettingsPublic:
    """Get the configuration."""
    policy_versions = await fetch_policy_versions()
    return SettingsPublic(
        remote_client_url=settings.remote_client_url,
        remote_api_url=settings.remote_api_url,
        github_client_id=settings.github_client_id,
        google_client_id=settings.google_client_id,
        environment=settings.environment,
        experimental=settings.experimental,
        privacy_version=policy_versions["privacyVersion"],
        terms_version=policy_versions["termsVersion"],
    )
