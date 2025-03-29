"""The `lillypad` package."""

import importlib.metadata

from . import ee as ee
from . import server as server

__version__ = importlib.metadata.version("lilypad")


__all__ = [
    "ee",
    "server",
]
