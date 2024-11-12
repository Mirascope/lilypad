"""Utility functions for working with spans."""

import json
from collections.abc import Sequence
from typing import Any, Literal

from pydantic import BaseModel


class _TextPart(BaseModel):
    """Text part model."""

    type: Literal["text"]
    text: str


class _ImagePart(BaseModel):
    """Image part model."""

    type: Literal["image"]
    media_type: str
    image: str
    detail: str | None


class _AudioPart(BaseModel):
    """Image part model."""

    type: Literal["audio"]
    media_type: str
    audio: str


# TODO: Add support for tools
class MessageParam(BaseModel):
    """Message param model agnostic to providers."""

    role: str
    content: Sequence[_AudioPart | _TextPart | _ImagePart]


def group_span_keys(attributes: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Groups gen_ai related attributes into a structured format.

    Args:
        attributes (Dict[str, Any]): Dictionary containing gen_ai prefixed key-value pairs

    Returns:
        Dict[str, Dict[str, Any]]: Grouped and processed attributes

    Example:
        attributes = {
            "gen_ai.prompt.0.content": "Hello",
            "gen_ai.completion.0.content": "Hi there",
            "gen_ai.completion.0.tool_calls.0.name": "search"
        }
    """
    grouped_items = {}
    message_index = 0

    for key, value in attributes.items():
        # Only process gen_ai related keys
        if not key.startswith("gen_ai."):
            continue

        # Remove the "gen_ai" prefix for easier processing
        key_without_prefix = key[len("gen_ai.") :]
        key_parts = key_without_prefix.split(".")
        # Get the base category (prompt or completion) and its index
        if len(key_parts) < 3:  # We need at least category, index, and field
            continue
        item_category = key_parts[0]
        item_index = key_parts[1]

        if item_category not in ["prompt", "completion"]:
            continue

        # Create the group key
        group_key = f"{item_category}.{item_index}"

        # Initialize group if it doesn't exist
        if group_key not in grouped_items:
            grouped_items[group_key] = {"index": message_index}
            message_index += 1

        # Handle tool_calls specially
        if len(key_parts) > 2 and key_parts[2] == "tool_calls":
            tool_call_index = int(key_parts[3])
            tool_call_field = key_parts[4]

            # Initialize tool_calls list if it doesn't exist
            if "tool_calls" not in grouped_items[group_key]:
                grouped_items[group_key]["tool_calls"] = []

            # Extend tool_calls list if needed
            while len(grouped_items[group_key]["tool_calls"]) <= tool_call_index:
                grouped_items[group_key]["tool_calls"].append({})

            # Parse JSON arguments if present
            if tool_call_field == "arguments" and isinstance(value, str):
                try:
                    grouped_items[group_key]["tool_calls"][tool_call_index][
                        tool_call_field
                    ] = json.loads(value)
                except json.JSONDecodeError:
                    grouped_items[group_key]["tool_calls"][tool_call_index][
                        tool_call_field
                    ] = value
            else:
                grouped_items[group_key]["tool_calls"][tool_call_index][
                    tool_call_field
                ] = value
        else:
            # Handle regular fields
            grouped_items[group_key][key_parts[2]] = value

    return grouped_items


def convert_gemini_messages(
    messages: dict[str, Any],
) -> list[MessageParam]:
    """Convert Gemini messages."""
    structured_messages: list[MessageParam] = []
    for key, value in messages.items():
        if key.startswith("prompt"):
            content = []
            for part in json.loads(value["user"]):
                if isinstance(part, str):
                    content.append(_TextPart(type="text", text=part))
                elif isinstance(part, dict):
                    if part.get("mime_type", "").startswith("image"):
                        content.append(
                            _ImagePart(
                                type="image",
                                media_type=part["mime_type"],
                                image=part["data"],
                                detail=None,
                            )
                        )
                    elif part.get("mime_type", "").startswith("audio"):
                        content.append(
                            _AudioPart(
                                type="audio",
                                media_type=part["mime_type"],
                                audio=part["data"],
                            )
                        )
            structured_messages.append(
                MessageParam(
                    content=content,
                    role="user",
                )
            )
        elif key.startswith("completion"):
            structured_messages.append(
                MessageParam(
                    content=[_TextPart(type="text", text=value["content"])],
                    role="assistant",
                )
            )
    return structured_messages


def convert_anthropic_messages(
    messages: dict[str, Any],
) -> list[MessageParam]:
    """Convert Anthropic messages."""
    structured_messages: list[MessageParam] = []
    for key, value in messages.items():
        if key.startswith("prompt"):
            content = []
            try:
                for part in json.loads(value["content"]):
                    if isinstance(part, str):
                        content.append(_TextPart(type="text", text=part))
                    elif isinstance(part, dict):
                        if part.get("type", "") == "image":
                            content.append(
                                _ImagePart(
                                    type="image",
                                    media_type=part["source"]["media_type"],
                                    image=part["source"]["data"],
                                    detail=None,
                                )
                            )
                        else:
                            content.append(_TextPart(type="text", text=part["text"]))
            except json.JSONDecodeError:
                content.append(_TextPart(type="text", text=value["content"]))

            structured_messages.append(
                MessageParam(
                    content=content,
                    role="user",
                )
            )
        elif key.startswith("completion"):
            content = []
            part = value.get("content", None)
            if isinstance(part, str):
                content.append(_TextPart(type="text", text=part))
            elif isinstance(part, dict):
                content.append(_TextPart(type="text", text=part["text"]))
            if _ := value.get("tool_calls", []):  # TODO: Add support for tool calls
                pass
            if len(content) > 0:
                structured_messages.append(
                    MessageParam(
                        content=content,
                        role="assistant",
                    )
                )
    return structured_messages
