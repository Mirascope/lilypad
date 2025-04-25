"""Spans schemas."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

import httpx
from cachetools.func import ttl_cache
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from pydantic import BaseModel

from ..models.spans import Scope, SpanTable
from ..schemas.tags import TagPublic
from .functions import Provider


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


def convert_azure_messages(
    messages: list[dict[str, Any]],
) -> list[MessageParam]:
    """Convert Azure OpenTelemetry messages to BaseModel."""
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
    """Convert Mirascope OpenTelemetry messages to BaseModel."""
    new_messages: list[dict[str, Any]] = (
        json.loads(messages) if isinstance(messages, str) else messages
    )
    structured_messages: list[MessageParam] = []

    def handle_text_content(role: str, text: str) -> MessageParam:
        """Create a MessageParam with text content."""
        return MessageParam(role=role, content=[_TextPart(type="text", text=text)])

    def handle_media_content(role: str, media_content: dict) -> MessageParam | None:
        """Create a MessageParam with media content (image or audio)."""
        if media_content.get("type") == "image":
            return MessageParam(
                role=role,
                content=[
                    _ImagePart(
                        type="image",
                        media_type=media_content["media_type"],
                        image=media_content["image"],
                        detail=media_content.get("detail"),
                    )
                ],
            )
        elif media_content.get("type") == "audio":
            return MessageParam(
                role=role,
                content=[
                    _AudioPart(
                        type="audio",
                        media_type=media_content["media_type"],
                        audio=media_content["audio"],
                    )
                ],
            )
        return None  # Unsupported media type

    def handle_tool_call(tool_call: dict) -> _ToolCall:
        """Convert a tool call dict to a _ToolCall object."""
        return _ToolCall(
            type="tool_call",
            name=tool_call.get("name", ""),
            arguments=dict(tool_call.get("args", {}).items()),
        )

    for message in new_messages:
        role = message.get("role", "")
        content = message.get("content")

        # Handle text content (for user, system, assistant, tool roles)
        if isinstance(content, str):
            structured_messages.append(handle_text_content(role, content))

        # Handle media content (for user and system roles)
        elif isinstance(content, dict) and role in ["user", "system"]:
            media_message = handle_media_content(role, content)
            if media_message:
                structured_messages.append(media_message)

        # Handle assistant with tool calls
        elif role == "assistant" and isinstance(content, list):
            content_parts = []
            for content_item in content:
                if (
                    isinstance(content_item, dict)
                    and content_item.get("type") == "tool_call"
                ):
                    content_parts.append(handle_tool_call(content_item))
                elif isinstance(content_item, str):
                    content_parts.append(_TextPart(type="text", text=content_item))

            if content_parts:
                structured_messages.append(
                    MessageParam(
                        role="assistant",
                        content=content_parts,
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
    attributes: dict[str, Any] = event.get("attributes", {})
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


class SpanMoreDetails(BaseModel):
    """Span more details model."""

    uuid: UUID
    project_uuid: UUID | None = None
    function_uuid: UUID | None = None
    display_name: str
    provider: str
    model: str
    scope: Scope
    input_tokens: float | None = None
    output_tokens: float | None = None
    duration_ms: float | None = None
    signature: str | None = None
    code: str | None = None
    arg_values: dict[str, Any] | None = None
    output: str | None = None
    messages: list[MessageParam]
    data: dict[str, Any]
    cost: float | None = None
    template: str | None = None
    status: str | None = None
    events: list[Event] | None = None
    tags: list[TagPublic] | None = None

    @classmethod
    def from_span(cls, span: SpanTable) -> SpanMoreDetails:
        """Create a SpanMoreDetails object from a SpanTable object."""
        data = span.data
        messages = []
        signature = None
        code = None
        arg_values = None
        output = None
        template = None
        status = data.get("status")
        attributes: dict = data["attributes"]
        display_name = data["name"]
        events = convert_events(data.get("events", []))
        if span.scope == Scope.LLM:
            provider = attributes.get(gen_ai_attributes.GEN_AI_SYSTEM, "unknown")
            if provider in (Provider.GEMINI.value, "google_genai"):
                messages = convert_gemini_messages(data["events"])
            elif (
                provider == Provider.OPENROUTER.value
                or provider == Provider.OPENAI.value
            ):
                messages = convert_openai_messages(data["events"])
            elif provider == Provider.ANTHROPIC.value:
                messages = convert_anthropic_messages(data["events"])
        else:
            lilypad_type = attributes.get("lilypad.type")
            if lilypad_type:
                signature = attributes.get(f"lilypad.{lilypad_type}.signature", None)
                code = attributes.get(f"lilypad.{lilypad_type}.code", None)
                arg_values = json.loads(
                    attributes.get(f"lilypad.{lilypad_type}.arg_values", "{}")
                )
                output = attributes.get(f"lilypad.{lilypad_type}.output", None)
                messages = convert_mirascope_messages(
                    attributes.get(f"lilypad.{lilypad_type}.common_messages", [])
                )
                template = attributes.get(f"lilypad.{lilypad_type}.template", None)
        if not span.uuid:
            raise ValueError("UUID does not exist.")
        return SpanMoreDetails.model_validate(
            {
                **span.model_dump(),
                "tags": span.tags,
                "display_name": display_name,
                "model": attributes.get(
                    gen_ai_attributes.GEN_AI_REQUEST_MODEL, "unknown"
                ),
                "provider": attributes.get(gen_ai_attributes.GEN_AI_SYSTEM, "unknown"),
                "signature": signature,
                "code": code,
                "arg_values": arg_values,
                "output": output,
                "messages": messages,
                "template": template,
                "data": data,
                "status": status,
                "events": events,
            },
        )
