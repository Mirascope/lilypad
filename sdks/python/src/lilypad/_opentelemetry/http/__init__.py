"""HTTP client instrumentation for distributed tracing."""

from .auto_instrument import (
    instrument_http_clients,
    instrument_requests,
    instrument_httpx,
    instrument_aiohttp,
    instrument_urllib3,
    uninstrument_http_clients,
    uninstrument_requests,
    uninstrument_httpx,
    uninstrument_aiohttp,
    uninstrument_urllib3,
)

__all__ = [
    "instrument_aiohttp",
    "instrument_http_clients",
    "instrument_httpx",
    "instrument_requests",
    "instrument_urllib3",
    "uninstrument_aiohttp",
    "uninstrument_http_clients",
    "uninstrument_httpx",
    "uninstrument_requests",
    "uninstrument_urllib3",
]
