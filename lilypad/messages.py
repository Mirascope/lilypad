"""The lilypad `Message` complex return type."""

import asyncio
import inspect
from collections.abc import Coroutine
from typing import Any, Generic

from mirascope.core import base as mb
from pydantic._internal._model_construction import ModelMetaclass
from typing_extensions import TypeVarTuple, Unpack

_ToolsT = TypeVarTuple("_ToolsT")


class _DelegateAbstractMethods(ModelMetaclass):
    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        cls = super().__new__(mcls, name, bases, namespace)
        cls.__abstractmethods__ = frozenset()
        return cls


class Message(
    mb.BaseCallResponse[
        Any, mb.BaseTool, Any, mb.BaseDynamicConfig, Any, mb.BaseCallParams, Any
    ],
    Generic[Unpack[_ToolsT]],
    metaclass=_DelegateAbstractMethods,
):
    """The return type for more complex LLM interactions."""

    _response: mb.BaseCallResponse

    def __init__(self, response: mb.BaseCallResponse) -> None:
        self._response = response
        for attr_name, attr_value in vars(response).items():
            setattr(self, attr_name, attr_value)

    def __getattr__(self, name: str) -> Any:
        """Delegate any unknown attributes/methods to the concrete instance"""
        return getattr(self._response, name)

    def call_tools(self) -> list[Any] | Coroutine[Any, Any, list[Any]]:
        """Returns the tool message parameters constructed from calling each tool."""
        if not (tools := self.tools):
            return []
        if inspect.iscoroutinefunction(tools[0].call):

            async def construct_tool_calls() -> list[Any]:
                outputs = await asyncio.gather(*[tool.call() for tool in tools])
                return list(zip(tools, outputs, strict=True))

            return construct_tool_calls()
        return self.tool_message_params([(tool, tool.call()) for tool in tools])


__all__ = ["Message"]
