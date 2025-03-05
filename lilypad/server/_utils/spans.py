"""Utility functions for working with spans."""

import json
from datetime import datetime
from typing import Any, Literal

import httpx
from cachetools.func import ttl_cache
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


class _ToolCall(BaseModel):
    """Image part model."""

    type: Literal["tool_call"]
    name: str
    arguments: dict[str, Any]


# TODO: Add support for tools
class MessageParam(BaseModel):
    """Message param model agnostic to providers."""

    role: str
    content: list[_AudioPart | _TextPart | _ImagePart | _ToolCall]


class Event(BaseModel):
    """Event model."""

    name: str
    type: str
    message: str
    timestamp: datetime


def convert_gemini_messages(
    messages: list[dict[str, Any]],
) -> list[MessageParam]:
    """Convert Gemini OpenTelemetry messages to BaseModel."""
    structured_messages: list[MessageParam] = []
    assistant_message = MessageParam(
        content=[],
        role="assistant",
    )
    for message in messages:
        name = message.get("name")
        if (
            name == "gen_ai.user.message"
            and (attributes := message.get("attributes", {}))
            and (content := attributes.get("content"))
        ):
            user_content = []
            try:
                for part in json.loads(content):
                    if isinstance(part, str):
                        user_content.append(_TextPart(type="text", text=part))
                    elif isinstance(part, dict):
                        if part.get("mime_type", "").startswith("image"):
                            user_content.append(
                                _ImagePart(
                                    type="image",
                                    media_type=part["mime_type"],
                                    image=part["data"],
                                    detail=None,
                                )
                            )
                        elif part.get("mime_type", "").startswith("audio"):
                            user_content.append(
                                _AudioPart(
                                    type="audio",
                                    media_type=part["mime_type"],
                                    audio=part["data"],
                                )
                            )
            except json.JSONDecodeError:
                user_content.append(_TextPart(type="text", text=content))
            structured_messages.append(
                MessageParam(
                    content=user_content,
                    role="user",
                )
            )
        elif name == "gen_ai.choice":
            attributes = message.get("attributes", {})
            index = attributes["index"]
            if len(assistant_message.content) <= index:
                assistant_message.content.append(_TextPart(type="text", text=""))
            attribute_message = json.loads(attributes.get("message", "{}"))
            if content := attribute_message.get("content"):
                for c in content:
                    assistant_message.content[index].text += c
            if tool_calls := attribute_message.get("tool_calls"):
                for tool_call in tool_calls:
                    function: dict = tool_call.get("function", {})
                    assistant_message.content.append(
                        _ToolCall(
                            type="tool_call",
                            name=function.get("name", ""),
                            arguments=function.get("arguments", {}),
                        )
                    )
    structured_messages.append(assistant_message)
    return structured_messages


def convert_openai_messages(
    messages: list[dict[str, Any]],
) -> list[MessageParam]:
    """Convert OpenAI OpenTelemetry messages to BaseModel."""
    structured_messages: list[MessageParam] = []
    assistant_message = MessageParam(
        content=[],
        role="assistant",
    )

    for message in messages:
        name = message.get("name")
        if (
            name == "gen_ai.user.message"
            and (attributes := message.get("attributes", {}))
            and (content := attributes.get("content"))
        ):
            user_content = []
            try:
                for part in json.loads(content):
                    if isinstance(part, str):
                        user_content.append(_TextPart(type="text", text=part))
                    elif isinstance(part, dict):
                        if part.get("type", "") == "image_url":
                            img_url = part["image_url"]["url"]
                            # Strip data:image/ and ;base64 from the image_url
                            media = img_url.split("data:image/")[1].split(";")
                            media_type = media[0]
                            img = media[1].split(",")[1]
                            user_content.append(
                                _ImagePart(
                                    type="image",
                                    media_type=f"image/{media_type}",
                                    image=img,
                                    detail=part["image_url"]["detail"],
                                )
                            )
                        else:
                            user_content.append(
                                _TextPart(type="text", text=part["text"])
                            )
            except json.JSONDecodeError:
                user_content.append(_TextPart(type="text", text=content))

            structured_messages.append(
                MessageParam(
                    content=user_content,
                    role="user",
                )
            )
        elif name == "gen_ai.choice":
            attributes = message.get("attributes", {})
            index = attributes["index"]
            attribute_message: dict = json.loads(attributes.get("message", "{}"))
            if tool_calls := attribute_message.get("tool_calls"):
                for tool_call in tool_calls:
                    function: dict = tool_call.get("function", {})
                    assistant_message.content.append(
                        _ToolCall(
                            type="tool_call",
                            name=function.get("name", ""),
                            arguments=json.loads(function.get("arguments", "{}")),
                        )
                    )
            elif len(assistant_message.content) <= index and attribute_message.get(
                "content"
            ):
                assistant_message.content.append(_TextPart(type="text", text=""))
                try:
                    content = str(json.loads(attribute_message.get("content", "{}")))
                except json.JSONDecodeError:
                    content = attribute_message.get("content", "")
                assistant_message.content[index].text += content
    structured_messages.append(assistant_message)
    return structured_messages


def convert_anthropic_messages(
    messages: list[dict[str, Any]],
) -> list[MessageParam]:
    """Convert Anthropic OpenTelemetry messages to BaseModel."""
    structured_messages: list[MessageParam] = []
    assistant_message = MessageParam(
        content=[],
        role="assistant",
    )
    for message in messages:
        name = message.get("name")
        if (
            name == "gen_ai.user.message"
            and (attributes := message.get("attributes", {}))
            and (content := attributes.get("content"))
        ):
            user_content = []
            try:
                for part in json.loads(content):
                    if isinstance(part, str):
                        user_content.append(_TextPart(type="text", text=part))
                    elif isinstance(part, dict):
                        if part.get("type", "") == "image":
                            user_content.append(
                                _ImagePart(
                                    type="image",
                                    media_type=part["source"]["media_type"],
                                    image=part["source"]["data"],
                                    detail=None,
                                )
                            )
                        else:
                            user_content.append(
                                _TextPart(type="text", text=part["text"])
                            )
            except json.JSONDecodeError:
                user_content.append(_TextPart(type="text", text=content))

            structured_messages.append(
                MessageParam(
                    content=user_content,
                    role="user",
                )
            )
        elif name == "gen_ai.choice":
            attributes = message.get("attributes", {})
            index = attributes.get("index")
            if index is not None and len(assistant_message.content) <= index:
                assistant_message.content.append(_TextPart(type="text", text=""))
                attribute_message = json.loads(attributes.get("message", "{}"))
                content = attribute_message.get("content", "{}")
                for c in content:
                    assistant_message.content[index].text += c
            else:
                attribute_message = json.loads(attributes.get("message", "{}"))
                if content := attribute_message.get("content"):
                    assistant_message.content = [_TextPart(type="text", text=content)]
                elif tool_calls := attribute_message.get("tool_calls"):
                    function = tool_calls.get("function", {})
                    assistant_message.content.append(
                        _ToolCall(
                            type="tool_call",
                            name=function.get("name", ""),
                            arguments=function.get("arguments", {}),
                        )
                    )
    structured_messages.append(assistant_message)
    return structured_messages


def convert_mirascope_messages(
    messages: list[dict[str, Any]] | str,
) -> list[MessageParam]:
    new_messages: list[dict[str, Any]] = (
        json.loads(messages) if isinstance(messages, str) else messages
    )
    structured_messages: list[MessageParam] = []
    for message in new_messages:
        if message.get("role") == "user":
            if isinstance(message.get("content"), str):
                structured_messages.append(
                    MessageParam(
                        role="user",
                        content=[_TextPart(type="text", text=message["content"])],
                    )
                )
            elif isinstance(message.get("content"), dict):
                if message["content"].get("type") == "image":
                    structured_messages.append(
                        MessageParam(
                            role="user",
                            content=[
                                _ImagePart(
                                    type="image",
                                    media_type=message["content"]["media_type"],
                                    image=message["content"]["image"],
                                    detail=message["content"].get("detail"),
                                )
                            ],
                        )
                    )
                elif message["content"].get("type") == "audio":
                    structured_messages.append(
                        MessageParam(
                            role="user",
                            content=[
                                _AudioPart(
                                    type="audio",
                                    media_type=message["content"]["media_type"],
                                    audio=message["content"]["audio"],
                                )
                            ],
                        )
                    )
        elif message.get("role") == "system":
            if isinstance(message.get("content"), str):
                structured_messages.append(
                    MessageParam(
                        role="system",
                        content=[_TextPart(type="text", text=message["content"])],
                    )
                )
            elif isinstance(message.get("content"), dict):
                if message["content"].get("type") == "image":
                    structured_messages.append(
                        MessageParam(
                            role="system",
                            content=[
                                _ImagePart(
                                    type="image",
                                    media_type=message["content"]["media_type"],
                                    image=message["content"]["image"],
                                    detail=message["content"].get("detail"),
                                )
                            ],
                        )
                    )
                elif message["content"].get("type") == "audio":
                    structured_messages.append(
                        MessageParam(
                            role="system",
                            content=[
                                _AudioPart(
                                    type="audio",
                                    media_type=message["content"]["media_type"],
                                    audio=message["content"]["audio"],
                                )
                            ],
                        )
                    )

    return structured_messages


def _convert_timestamp(ns_timestamp: int) -> datetime:
    """Convert nanosecond timestamp to datetime."""
    # Convert nanoseconds to seconds and maintain microsecond precision
    seconds = ns_timestamp // 1_000_000_000
    microseconds = (ns_timestamp % 1_000_000_000) // 1000
    return datetime.fromtimestamp(seconds).replace(microsecond=microseconds)


def _extract_event_attribute(event: dict, field: str) -> str:
    """Extract an attribute from an event using its name as prefix."""
    event_name = event.get("name", "unknown")
    attributes = event.get("attributes", {})
    return attributes.get(f"{event_name}.{field}", "")


def convert_events(events: list[dict[str, Any]]) -> list[Event]:
    """Convert events to Event model."""
    return [
        Event(
            name=event.get("name", "unknown"),
            timestamp=_convert_timestamp(event.get("timestamp", 0)),
            type=_extract_event_attribute(event, "type") or "unknown",
            message=_extract_event_attribute(event, "message"),
        )
        for event in events
    ]


@ttl_cache(maxsize=128, ttl=86400)  # Cache up to 128 items for 24 hours
async def fetch_with_memory_cache(url: str) -> dict:
    """Fetch data from a URL and cache it in memory for 24 hours."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()


async def calculate_openrouter_cost(
    input_tokens: int | float | None,
    output_tokens: int | float | None,
    model: str,
) -> float | None:
    """Calculate the cost of a completion using OpenRouter API."""
    if input_tokens is None or output_tokens is None:
        return None
    data = await fetch_with_memory_cache("https://openrouter.ai/api/v1/models")
    model_pricing: dict[str, float | None] = {
        "prompt": None,
        "completion": None,
    }
    for openrouter_model in data["data"]:
        if openrouter_model["id"] == model:
            pricing: dict = openrouter_model["pricing"]
            model_pricing["prompt"] = (
                float(pricing["prompt"]) if pricing.get("prompt") else None
            )
            model_pricing["completion"] = (
                float(pricing["completion"]) if pricing.get("completion") else None
            )
            break
    if model_pricing["prompt"] and model_pricing["completion"]:
        prompt_cost = input_tokens * model_pricing["prompt"]
        completion_cost = output_tokens * model_pricing["completion"]
        return prompt_cost + completion_cost
    return None
