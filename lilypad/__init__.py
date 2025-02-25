"""The `lillypad` package."""

import importlib.metadata

from . import ee as ee
from . import server as server
from ._configure import configure
from .generations import generation
from .messages import Message
from .prompts import prompt
from .response_models import response_model
from .tools import tool

__version__ = importlib.metadata.version("python-lilypad")


__all__ = [
    "configure",
    "ee",
    "generation",
    "Message",
    "prompt",
    "server",
    "tool",
    "response_model",
]
