"""A module for handling OpenAI related utilities."""

import inspect
from collections.abc import Callable
from typing import cast

from mirascope.core.base import BaseMessageParam, BasePrompt, BaseTool, _utils
from mirascope.core.openai import OpenAITool
from mirascope.core.openai._utils import convert_message_params
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam


def messages(prompt: BasePrompt) -> list[ChatCompletionMessageParam]:
    """Returns messages for the OpenAI API."""
    message_params = cast(
        list[BaseMessageParam | ChatCompletionMessageParam], prompt.message_params()
    )
    return convert_message_params(message_params)


def tools(tools: list[BaseTool | Callable] | None) -> list[ChatCompletionToolParam]:
    """Returns tools for the OpenAI API."""
    return [
        _utils.convert_base_model_to_base_tool(tool, OpenAITool).tool_schema()
        if inspect.isclass(tool)
        else _utils.convert_function_to_base_tool(tool, OpenAITool).tool_schema()  # pyright: ignore [reportArgumentType]
        for tool in tools or []
    ]


__all__ = ["messages"]
