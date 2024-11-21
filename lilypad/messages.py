"""The lilypad `Message` complex return type."""

import asyncio
import inspect
from collections.abc import Coroutine
from types import GenericAlias
from typing import Any, ClassVar, Generic

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
        Any,
        mb.BaseTool,
        Any,
        mb.BaseDynamicConfig[Any, Any, Any],
        Any,
        mb.BaseCallParams,
        Any,
    ],
    Generic[Unpack[_ToolsT]],
    metaclass=_DelegateAbstractMethods,
):
    """The return type for more complex LLM interactions."""

    _response: mb.BaseCallResponse
    __parameters__ = (_ToolsT,)
    __orig_bases__: ClassVar[tuple[Any, ...]]

    def __init__(self, response: mb.BaseCallResponse) -> None:
        super().__init__(
            **{key: getattr(response, key) for key in response.model_fields}
        )
        object.__setattr__(self, "_response", response)

    @classmethod
    def __class_getitem__(cls, params: Any) -> GenericAlias:  # pyright: ignore [reportIncompatibleMethodOverride]
        """Return a properly constructed _GenericAlias instead of a new class."""
        if not isinstance(params, tuple):
            params = (params,)
        return GenericAlias(cls, params)

    def __getattribute__(self, name: str) -> Any:
        """Override attribute access to check wrapped response first."""
        special_names = {
            "_response",
            "__dict__",
            "__class__",
            "model_fields",
            "__annotations__",
            "__pydantic_validator__",
            "__pydantic_fields_set__",
            "__pydantic_extra__",
            "__pydantic_private__",
            "__class_getitem__",
        }

        if name in special_names:
            return object.__getattribute__(self, name)

        try:
            response = object.__getattribute__(self, "_response")
            return getattr(response, name)
        except AttributeError:
            return object.__getattribute__(self, name)

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
