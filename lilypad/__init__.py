"""The lillypad package."""

from contextlib import suppress

from .prompts import prompt
from .tools import tools
from .trace import trace

with suppress(ImportError):
    from . import openai as openai


__all__ = ["openai", "prompt", "tools", "trace"]
