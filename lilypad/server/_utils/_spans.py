"""Utility functions for working with spans."""

import json
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
    content: list[_AudioPart | _TextPart | _ImagePart]


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
            content = attribute_message.get("content", "{}")
            for c in content:
                assistant_message.content[index].text += c
    structured_messages.append(assistant_message)
    return structured_messages


def convert_openai_messages(
    messages: list[dict[str, Any]],
) -> list[MessageParam]:
    """Convert Anthropic messages."""
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
                        user_content.append(_TextPart(type="text", text=part["text"]))

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
            content = json.loads(attribute_message.get("content", "{}"))
            assistant_message.content[index].text += content
    structured_messages.append(assistant_message)
    return structured_messages


def convert_anthropic_messages(
    messages: list[dict[str, Any]],
) -> list[MessageParam]:
    """Convert Anthropic messages."""
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
                        user_content.append(_TextPart(type="text", text=part["text"]))

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
            content = attribute_message.get("content", "{}")
            for c in content:
                assistant_message.content[index].text += c
    structured_messages.append(assistant_message)
    return structured_messages
