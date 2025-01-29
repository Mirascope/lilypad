"""The `lillypad` package."""

import importlib.metadata
from contextlib import suppress

from . import ee as ee
from . import server as server
from ._configure import configure
from .generations import generation
from .messages import Message
from .prompts import prompt
from .response_models import response_model
from .tools import tool

with suppress(ImportError):
    import ee.evals as evals

__version__ = importlib.metadata.version("python-lilypad")


__all__ = [
    "configure",
    "ee",
    "evals",
    "generation",
    "Message",
    "prompt",
    "server",
    "tool",
    "response_model",
]
