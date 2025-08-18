"""Global test configuration for lilypad tests.

This module provides shared fixtures and configuration for all tests in the
lilypad test suite, including VCR configuration for HTTP recording/playback.
"""

import pytest
from typing import Callable
from typing_extensions import TypedDict


class Response(TypedDict):
    """Response from an HTTP request."""

    headers: dict[str, str]
    """Response headers."""


class VCRConfig(TypedDict):
    """Configuration for VCR.py HTTP recording and playback.

    VCR.py is used to record HTTP interactions during tests and replay them
    in subsequent test runs, making tests faster and more reliable.
    """

    record_mode: str
    """How VCR should handle recording. 'once' means record once then replay.
    
    Options:
    - 'once': Record interactions once, then always replay from cassette
    - 'new_episodes': Record new interactions, replay existing ones
    - 'all': Always record, overwriting existing cassettes
    - 'none': Never record, only replay (will fail if cassette missing)
    """

    match_on: list[str]
    """HTTP request attributes to match when finding recorded interactions.
    
    Common options:
    - 'method': HTTP method (GET, POST, etc.)
    - 'uri': Request URI/URL
    - 'body': Request body content
    - 'headers': Request headers
    """

    filter_headers: list[str]
    """Headers to filter out from recordings for security/privacy.
    
    These headers will be removed from both recorded cassettes and
    when matching requests during playback. Commonly used for:
    - Authentication tokens
    - API keys
    - Organization identifiers
    """

    filter_post_data_parameters: list[str]
    """POST data parameters to filter out from recordings.
    
    Similar to filter_headers but for form data and request body parameters.
    Useful for removing sensitive data from request bodies.
    """

    filter_query_parameters: list[str]
    """Query parameters to filter out from recordings.
    
    Filters out specified query parameters from the URL.
    Useful for removing API keys that are passed as query parameters.
    """

    before_record_response: Callable[[Response], Response]
    """Callback to modify response before recording.
    
    This function is called with the response dictionary before it's saved
    to the cassette. It can be used to filter out sensitive response headers
    or modify response data. Returns the modified response dictionary.
    """


def _filter_response_headers(response: Response) -> Response:
    """Filter sensitive headers from response before recording."""

    sensitive_headers = {
        "openai-organization",
        "openai-project",
        "anthropic-organization-id",
        "cf-ray",
        "x-request-id",
        "x-ms-client-request-id",
        "x-ms-request-id",
        "request-id",
        "set-cookie",
        "x-stainless-arch",
        "x-stainless-os",
        "x-stainless-runtime-version",
    }

    filtered_headers = {
        k: v
        for k, v in response["headers"].items()
        if k.lower() not in sensitive_headers
    }

    return {**response, "headers": filtered_headers}


@pytest.fixture(scope="session")
def vcr_config() -> VCRConfig:
    """VCR configuration for all API tests.

    Uses session scope since VCR configuration is static and can be shared
    across all test modules in a session. This covers all major LLM providers:
    - OpenAI (authorization header)
    - Google/Gemini (x-goog-api-key header, key query parameter)
    - Anthropic (x-api-key, anthropic-organization-id headers)
    - Azure AI Inference (api-key header)

    Returns:
        VCRConfig: Dictionary with VCR.py configuration settings
    """
    return {
        "record_mode": "once",
        "match_on": ["method", "uri", "body"],
        "filter_headers": [
            "authorization",
            "x-api-key",
            "api-key",
            "x-goog-api-key",
            "anthropic-organization-id",
            "openai-organization",
            "openai-project",
            "cf-ray",
            "x-request-id",
            "x-ms-client-request-id",
            "request-id",
            "set-cookie",
            "x-stainless-arch",
            "x-stainless-os",
            "x-stainless-runtime-version",
        ],
        "filter_post_data_parameters": [],
        "filter_query_parameters": ["key"],
        "before_record_response": _filter_response_headers,
    }
