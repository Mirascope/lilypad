"""The lilypad `tool` decorator."""

from __future__ import annotations

from typing import Any, TypeVar, ParamSpec
from collections.abc import Callable

from mirascope.core import BaseTool
from mirascope.llm.tool import Tool as _Tool

_P = ParamSpec("_P")
_R = TypeVar("_R")


class Tool(_Tool):
    """The lilypad `Tool` class."""

    ...


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
