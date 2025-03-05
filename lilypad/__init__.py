"""The `lillypad` package."""

import importlib.metadata

from . import ee as ee
from . import server as server
from ._configure import configure
from .generations import generation
from .messages import Message
from .spans import span
from .tools import tool
from .traces import trace

__version__ = importlib.metadata.version("python-lilypad")


__all__ = [
    "configure",
    "ee",
    "generation",
    "Message",
    "server",
    "span",
    "tool",
    "trace",
]
