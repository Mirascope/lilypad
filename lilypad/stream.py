"""The `Stream` class of the `lilypad` package."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from typing import TYPE_CHECKING

from mirascope.llm.stream import Stream as _Stream

from .message_chunk import MessageChunk
from .tools import Tool

if TYPE_CHECKING:
    from . import Message


class Stream(_Stream):
    """The lilypad `Stream` class."""

    def __iter__(
        self,
    ) -> Generator[
        tuple[MessageChunk, Tool | None],
        None,
        None,
    ]:
        """Iterate over the stream."""
        for chunk, tool in super().__iter__():
            yield (
                MessageChunk(response=chunk),  # pyright: ignore [reportAbstractUsage]
                Tool(tool=tool) if tool is not None else None,  # pyright: ignore [reportAbstractUsage]
            )

    async def __aiter__(
        self,
    ) -> AsyncGenerator[
        tuple[MessageChunk, Tool | None],
        None,
    ]:
        """Iterates over the stream and stores useful information."""
        async for chunk, tool in super().__aiter__():
            yield (
                MessageChunk(response=chunk),  # pyright: ignore [reportAbstractUsage]
                Tool(tool=tool) if tool is not None else None,  # pyright: ignore [reportAbstractUsage]
            )

    def construct_call_response(
        self,
    ) -> Message:
        """Constructs a CallResponse instance."""
        return Message(super().construct_call_response())  # pyright: ignore [reportAbstractUsage]
