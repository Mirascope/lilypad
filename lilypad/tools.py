"""Utility for retrieving the tools for a function."""

import hashlib
import inspect
from collections.abc import Callable

from mirascope.core import BaseTool

from .dummy_database import get_dummy_database


def tools(fn: Callable) -> list[BaseTool | Callable]:
    """Returns the list of tools (or `None`) for `fn`."""
    unique_id = hashlib.sha256(
        f"{fn.__name__}:{inspect.signature(fn)}".encode()
    ).hexdigest()
    tools = get_dummy_database()[unique_id]["tools"]
    namespace = {"BaseTool": BaseTool}
    for tool in tools:
        exec(tool, namespace)
    return list(namespace.values())
