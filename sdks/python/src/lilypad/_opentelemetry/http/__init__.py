"""HTTP client instrumentation for distributed tracing."""

from .auto_instrument import (
    instrument_requests,
    instrument_httpx,
    instrument_aiohttp,
    instrument_urllib3,
    uninstrument_requests,
    uninstrument_httpx,
    uninstrument_aiohttp,
    uninstrument_urllib3,
)

__all__ = [
    "instrument_aiohttp",
    "instrument_httpx",
    "instrument_requests",
    "instrument_urllib3",
    "uninstrument_aiohttp",
    "uninstrument_httpx",
    "uninstrument_requests",
    "uninstrument_urllib3",
]
