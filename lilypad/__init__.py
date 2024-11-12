"""The `lillypad` package."""

import importlib.metadata

from . import server as server
from ._configure import configure
from .messages import Message
from .prompts import prompt
from .tools import tool
from .traces import trace

__version__ = importlib.metadata.version("python-lilypad")

__all__ = ["configure", "Message", "prompt", "server", "tool", "trace"]
