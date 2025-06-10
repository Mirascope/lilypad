"""Integrations for Lilypad distributed tracing.

This module provides integrations for automatic distributed tracing across
various HTTP clients and frameworks.
"""

# Import with error handling for optional components
__all__ = []

try:
    from .auto_instrument import instrument_http_clients

    __all__.append("instrument_http_clients")
except ImportError:
    pass

try:
    from .http_client import get_traced_http_client

    __all__.append("get_traced_http_client")
except ImportError:
    pass

# Import traced client classes if available
try:
    from .http_client import TracedRequestsSession

    __all__.append("TracedRequestsSession")
except ImportError:
    pass

try:
    from .http_client import TracedHTTPXClient, TracedAsyncHTTPXClient

    __all__.extend(["TracedAsyncHTTPXClient", "TracedHTTPXClient"])
except ImportError:
    pass

try:
    from .http_client import TracedAiohttpSession

    __all__.append("TracedAiohttpSession")
except ImportError:
    pass
