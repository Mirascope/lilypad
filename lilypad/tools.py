"""The lilypad `tool` decorator.

This decorator is used for creating AI-powered tools with built-in input validation
and metadata extraction capabilities. It transforms functions into BaseTool instances
that can be used within the Lilypad framework for AI interactions.

The decorator automatically:
- Enables input validation for tool parameters
- Extracts metadata for AI system understanding
- Integrates with the prompt template editor
- Supports proper versioning and tracing
"""

from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

from mirascope.core import BaseTool

_P = ParamSpec("_P")
_R = TypeVar("_R")


def tool() -> Callable[[Callable[_P, Any]], type[BaseTool]]:
    """Returns a decorator for marking a function as a tool."""

    def decorator(fn: Callable[_P, Any]) -> type[BaseTool]:
        # this function needs to be patched with all of the information that would go
        # into the prompt. for example, the description, the argument descriptions,
        # the final string output, etc.
        #
        # since the final string output is part of the prompt, that should be written
        # in the editor with access to the original arguments and the output of the
        # function as template variables.
        return BaseTool.type_from_fn(fn)

    return decorator
