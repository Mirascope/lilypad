"""The lilypad `Message` complex return type."""

from functools import cached_property

from pydantic import computed_field
from mirascope.llm.call_response import CallResponse

from .tools import Tool


class Message(CallResponse):
    """Message class for Lilypad response."""

    @computed_field
    @cached_property
    def tools(self) -> list[Tool] | None:  # pyright: ignore [reportIncompatibleVariableOverride]
        """The tools used in the response."""
        if tools := super().tools:
            return [Tool(tool) for tool in tools]  # pyright: ignore [reportAbstractUsage]
        return None


__all__ = ["Message"]
