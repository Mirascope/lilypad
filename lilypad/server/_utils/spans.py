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


def calculate_cost(
    input_tokens: int | float | None,
    output_tokens: int | float | None,
    system: str,
    model: str,
) -> float | None:
    """Calculate the cost of a completion using a provider API.

    https://openai.com/pricing

    Model                   Input               Output
    o1                      $15.00 / 1M tokens  $7.50 / 1M tokens   $60.00 / 1M tokens
    o1-2024-12-17           $15.00 / 1M tokens  $7.50 / 1M tokens   $60.00 / 1M tokens
    o1-preview-2024-09-12   $15.00 / 1M tokens  $7.50 / 1M tokens   $60.00 / 1M tokens
    o3-mini                 $1.10  / 1M tokens  $0.55 / 1M tokens   $4.40  / 1M tokens
    o3-mini-2025-01-31      $1.10  / 1M tokens  $0.55 / 1M tokens   $4.40  / 1M tokens
    o1-mini                 $1.10  / 1M tokens  $0.55 / 1M tokens   $4.40  / 1M tokens
    o1-mini-2024-09-12      $1.10  / 1M tokens  $0.55 / 1M tokens   $4.40  / 1M tokens
    gpt-4o-mini             $0.15 / 1M tokens   $0.60  / 1M tokens
    gpt-4o-mini-2024-07-18  $0.15 / 1M tokens   $0.60  / 1M tokens
    gpt-4o                  $2.50 / 1M tokens   $10.00 / 1M tokens
    gpt-4o-2024-08-06       $2.50 / 1M tokens   $10.00 / 1M tokens
    gpt-4o-2024-05-13       $5.00 / 1M tokens   $15.00 / 1M tokens
    gpt-4-turbo             $10.00 / 1M tokens  $30.00 / 1M tokens
    gpt-4-turbo-2024-04-09  $10.00 / 1M tokens  $30.00 / 1M tokens
    gpt-3.5-turbo-0125	    $0.50 / 1M tokens	$1.50 / 1M tokens
    gpt-3.5-turbo-1106	    $1.00 / 1M tokens	$2.00 / 1M tokens
    gpt-4-1106-preview	    $10.00 / 1M tokens 	$30.00 / 1M tokens
    gpt-4	                $30.00 / 1M tokens	$60.00 / 1M tokens
    text-embedding-3-small	$0.02 / 1M tokens
    text-embedding-3-large	$0.13 / 1M tokens
    text-embedding-ada-0002	$0.10 / 1M tokens

    https://www.anthropic.com/api

    claude-instant-1.2          $0.80 / 1M tokens   $2.40 / 1M tokens
    claude-2.0                  $8.00 / 1M tokens   $24.00 / 1M tokens
    claude-2.1                  $8.00 / 1M tokens   $24.00 / 1M tokens
    claude-3-haiku              $0.25 / 1M tokens   $1.25 / 1M tokens
    claude-3-sonnet             $3.00 / 1M tokens   $15.00 / 1M tokens
    claude-3-opus               $15.00 / 1M tokens   $75.00 / 1M tokens
    claude-3-5-haiku            $0.80 / 1M tokens   $4.00 / 1M tokens
    claude-3-5-sonnet           $3.00 / 1M tokens   $15.00 / 1M tokens
    """
    pricing = {
        "openai": {
            "o1": {
                "prompt": 0.000_015,
                "cached": 0.000_007_5,
                "completion": 0.000_06,
            },
            "o1-2024-12-17": {
                "prompt": 0.000_015,
                "cached": 0.000_007_5,
                "completion": 0.000_06,
            },
            "o1-preview-2024-09-12": {
                "prompt": 0.000_015,
                "cached": 0.000_007_5,
                "completion": 0.000_06,
            },
            "o3-mini": {
                "prompt": 0.000_001_1,
                "cached": 0.000_000_55,
                "completion": 0.000_004_4,
            },
            "o3-mini-2025-01-31": {
                "prompt": 0.000_001_1,
                "cached": 0.000_000_55,
                "completion": 0.000_004_4,
            },
            "o1-mini": {
                "prompt": 0.000_001_1,
                "cached": 0.000_000_55,
                "completion": 0.000_004_4,
            },
            "o1-mini-2024-09-12": {
                "prompt": 0.000_001_1,
                "cached": 0.000_000_55,
                "completion": 0.000_004_4,
            },
            "gpt-4o-mini": {
                "prompt": 0.000_000_15,
                "completion": 0.000_000_6,
            },
            "gpt-4o-mini-2024-07-18": {
                "prompt": 0.000_000_15,
                "completion": 0.000_000_6,
            },
            "gpt-4o": {
                "prompt": 0.000_002_5,
                "completion": 0.000_01,
            },
            "gpt-4o-2024-08-06": {
                "prompt": 0.000_002_5,
                "completion": 0.000_01,
            },
            "gpt-4o-2024-05-13": {
                "prompt": 0.000_005,
                "completion": 0.000_015,
            },
            "gpt-4-turbo": {
                "prompt": 0.000_01,
                "completion": 0.000_03,
            },
            "gpt-4-turbo-2024-04-09": {
                "prompt": 0.000_01,
                "completion": 0.000_03,
            },
            "gpt-3.5-turbo-0125": {
                "prompt": 0.000_000_5,
                "completion": 0.000_001_5,
            },
            "gpt-3.5-turbo-1106": {
                "prompt": 0.000_001,
                "completion": 0.000_002,
            },
            "gpt-4-1106-preview": {
                "prompt": 0.000_01,
                "completion": 0.000_03,
            },
            "gpt-4": {
                "prompt": 0.000_003,
                "completion": 0.000_006,
            },
            "gpt-3.5-turbo-4k": {
                "prompt": 0.000_015,
                "completion": 0.000_02,
            },
            "gpt-3.5-turbo-16k": {
                "prompt": 0.000_003,
                "completion": 0.000_004,
            },
            "gpt-4-8k": {
                "prompt": 0.000_003,
                "completion": 0.000_006,
            },
            "gpt-4-32k": {
                "prompt": 0.000_006,
                "completion": 0.000_012,
            },
            "text-embedding-3-small": {
                "prompt": 0.000_000_02,
                "completion": 0.000_000_02,
            },
            "text-embedding-ada-002": {
                "prompt": 0.000_000_1,
                "completion": 0.000_000_1,
            },
            "text-embedding-3-large": {
                "prompt": 0.000_000_13,
                "completion": 0.000_000_13,
            },
        },
        "anthropic": {
            "claude-instant-1.2": {
                "prompt": 0.000_000_8,
                "completion": 0.000_002_4,
            },
            "claude-2.0": {
                "prompt": 0.000_008,
                "completion": 0.000_024,
            },
            "claude-2.1": {
                "prompt": 0.000_008,
                "completion": 0.000_024,
            },
            "claude-3-haiku-20240307": {
                "prompt": 0.000_002_5,
                "completion": 0.000_012_5,
            },
            "claude-3-sonnet-20240229": {
                "prompt": 0.000_003,
                "completion": 0.000_015,
            },
            "claude-3-opus-20240229": {
                "prompt": 0.000_015,
                "completion": 0.000_075,
            },
            "claude-3-5-sonnet-20240620": {
                "prompt": 0.000_003,
                "completion": 0.000_015,
            },
            "claude-3-5-haiku-20241022": {
                "prompt": 0.000_008,
                "completion": 0.000_04,
            },
            "claude-3-5-sonnet-20241022": {
                "prompt": 0.000_003,
                "completion": 0.000_015,
            },
            # Bedrock models
            "anthropic.claude-3-haiku-20240307-v1:0": {
                "prompt": 0.000_002_5,
                "completion": 0.000_012_5,
            },
            "anthropic.claude-3-sonnet-20240229-v1:0": {
                "prompt": 0.000_003,
                "completion": 0.000_015,
            },
            "anthropic.claude-3-opus-20240229-v1:0": {
                "prompt": 0.000_015,
                "completion": 0.000_075,
            },
            "anthropic.claude-3-5-sonnet-20240620-v1:0": {
                "prompt": 0.000_003,
                "completion": 0.000_015,
            },
            # Vertex AI models
            "claude-3-haiku@20240307": {
                "prompt": 0.000_002_5,
                "completion": 0.000_012_5,
            },
            "claude-3-sonnet@20240229": {
                "prompt": 0.000_003,
                "completion": 0.000_015,
            },
            "claude-3-opus@20240229": {
                "prompt": 0.000_015,
                "completion": 0.000_075,
            },
            "claude-3-5-sonnet@20240620": {
                "prompt": 0.000_003,
                "completion": 0.000_015,
            },
        },
    }
    if input_tokens is None or output_tokens is None:
        return None

    try:
        model_pricing = pricing[system][model]
    except KeyError:
        return None

    prompt_cost = input_tokens * model_pricing["prompt"]
    completion_cost = output_tokens * model_pricing["completion"]
    total_cost = prompt_cost + completion_cost

    return total_cost


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
