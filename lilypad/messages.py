"""The lilypad `Message` complex return type."""

import asyncio
import inspect
from collections.abc import Coroutine
from typing import Any, Generic

from mirascope.core import base
from typing_extensions import TypeVarTuple, Unpack

_ToolsT = TypeVarTuple("_ToolsT")


class Message(Generic[Unpack[_ToolsT]]):
    """The return type for more complex LLM interactions."""

    response: base.BaseCallResponse

    def __init__(self, response: base.BaseCallResponse) -> None:
        """Initializes an instance of `Message`."""
        self.response = response

    @property
    def content(self) -> str:
        """Returns the string content of the response message."""
        return self.response.content

    def call_tools(self) -> list[Any] | Coroutine[Any, Any, list[Any]]:
        """Returns the tool message parameters constructed from calling each tool."""
        if not (tools := self.response.tools):
            return []
        if inspect.iscoroutinefunction(tools[0].call):

            async def construct_tool_calls() -> list[Any]:
                outputs = await asyncio.gather(*[tool.call() for tool in tools])
                return list(zip(tools, outputs, strict=True))

            return construct_tool_calls()
        return self.response.tool_message_params(
            [(tool, tool.call()) for tool in tools]
        )
