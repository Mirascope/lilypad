"""Utility functions for Google OpenTelemetry instrumentation.

This module provides helper functions for extracting and formatting Google AI
response data for telemetry purposes.
"""

from __future__ import annotations

import base64
import json
from enum import Enum
from io import BytesIO
from typing import Any, cast

import PIL
import PIL.WebPImagePlugin
from opentelemetry.trace import Span
from opentelemetry.util.types import AttributeValue
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from google.genai.types import (
    GenerateContentConfig,
    GenerateContentConfigDict,
    FinishReason,
    ContentUnionDict,
    ContentDict,
    Part,
    PartDict,
)
from ..utils import (
    BaseMetadata,
    set_server_address_and_port,
)
from ..types import (
    LLMOpenTelemetryFunctionCall,
    LLMOpenTelemetryMessage,
    LLMOpenTelemetryToolCall,
    LLMOpenTelemetryInlineData,
)
from google.genai.types import GenerateContentResponse, Content


class GoogleMetadata(BaseMetadata, total=False):
    model_version: str | None
    response_id: str | None
    safety_ratings: list[dict[str, Any]] | None
    citation_metadata: dict[str, Any] | None
    input_tokens: int
    output_tokens: int


def _extract_tool_names_from_config(
    config: GenerateContentConfigDict,
) -> list[str] | None:
    if not (tools := config.get("tools")):
        return None

    function_names: list[str] = []

    for tool in tools:
        if isinstance(tool, dict) and (
            function_declarations := tool.get("function_declarations")
        ):
            for declaration in function_declarations:
                if name := declaration.get("name"):
                    function_names.append(name)
    return function_names


def get_llm_request_attributes(
    kwargs: dict[str, Any],
    client: Any | None,
    operation_name: str = gen_ai_attributes.GenAiOperationNameValues.CHAT.value,
) -> dict[str, AttributeValue]:
    attributes: dict[str, AttributeValue] = {
        gen_ai_attributes.GEN_AI_SYSTEM: "google_genai",
        gen_ai_attributes.GEN_AI_REQUEST_MODEL: str(kwargs.get("model", "unknown")),
        gen_ai_attributes.GEN_AI_OPERATION_NAME: operation_name,
    }

    if client:
        set_server_address_and_port(client, attributes)

    config = cast(
        GenerateContentConfig | GenerateContentConfigDict | None, kwargs.get("config")
    )
    if config:
        if isinstance(config, GenerateContentConfig):
            config = cast(GenerateContentConfigDict, config.to_json_dict())
        if (temperature := config.get("temperature")) and temperature is not None:
            attributes[gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE] = temperature

        if (top_p := config.get("top_p")) and top_p is not None:
            attributes[gen_ai_attributes.GEN_AI_REQUEST_TOP_P] = top_p
        if (top_k := config.get("top_k")) and top_k is not None:
            attributes[gen_ai_attributes.GEN_AI_REQUEST_TOP_K] = top_k
        if max_output_tokens := config.get("max_output_tokens"):
            attributes[gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS] = max_output_tokens

        if stop_sequences := config.get("stop_sequences"):
            attributes[gen_ai_attributes.GEN_AI_REQUEST_STOP_SEQUENCES] = stop_sequences
        if "presence_penalty" in config and config["presence_penalty"] is not None:
            attributes[gen_ai_attributes.GEN_AI_REQUEST_PRESENCE_PENALTY] = config[
                "presence_penalty"
            ]
        if "frequency_penalty" in config and config["frequency_penalty"] is not None:
            attributes[gen_ai_attributes.GEN_AI_REQUEST_FREQUENCY_PENALTY] = config[
                "frequency_penalty"
            ]

        if function_names := _extract_tool_names_from_config(config):
            attributes["gen_ai.request.functions"] = tuple(function_names)

    return attributes


def set_response_attributes(
    span: Span,
    response: GenerateContentResponse,
    metadata: GoogleMetadata | None = None,
) -> None:
    attributes: dict[str, AttributeValue] = {}

    if response.model_version:
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_MODEL] = response.model_version

    if response.response_id:
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_ID] = response.response_id

    if response.usage_metadata:
        usage = response.usage_metadata
        if usage.prompt_token_count:
            attributes[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] = (
                usage.prompt_token_count
            )
        if usage.candidates_token_count:
            attributes[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] = (
                usage.candidates_token_count
            )

    if response.candidates:
        finish_reasons = []
        for candidate in response.candidates:
            if isinstance(candidate.finish_reason, Enum):
                finish_reasons.append(candidate.finish_reason.name)

        if finish_reasons:
            attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = tuple(
                finish_reasons
            )

    span.set_attributes(attributes)


def _convert_content_to_messages(
    contents: list[ContentUnionDict],
) -> list[LLMOpenTelemetryMessage]:
    messages: list[LLMOpenTelemetryMessage] = []

    for content in contents:
        if isinstance(content, str):
            messages.append(
                {
                    "role": "user",
                    "content": content,
                }
            )
        elif isinstance(content, Content):
            messages.append(
                _convert_content_dict_to_message(
                    cast(ContentDict, content.to_json_dict())
                )
            )
        elif isinstance(content, Part):
            messages.append(
                _convert_content_dict_to_message(
                    ContentDict(parts=[cast(PartDict, content.to_json_dict())])
                )
            )
        elif isinstance(content, PIL.WebPImagePlugin.WebPImageFile):
            buffered = BytesIO()
            content.save(buffered, format="WEBP")
            img_bytes = buffered.getvalue()

            messages.append(
                {
                    "role": "user",
                    "inline_data": [
                        {
                            "mime_type": "image/webp",
                            "data": base64.b64encode(img_bytes).decode("utf-8"),
                        }
                    ],
                }
            )

        elif isinstance(content, dict) and (parts := content.get("parts")):
            role = content.get("role")
            messages.append(
                _convert_content_dict_to_message(ContentDict(parts=parts, role=role))
            )

    return messages


def _convert_content_dict_to_message(
    content: ContentDict,
) -> LLMOpenTelemetryMessage:
    message: LLMOpenTelemetryMessage = {
        "role": content.get("role") or "user",
    }

    parts = content.get("parts") or []
    text_parts: list[str] = []
    inline_data: list[LLMOpenTelemetryInlineData] = []
    tool_calls: list[LLMOpenTelemetryToolCall] = []

    for part in parts:
        if text := part.get("text"):
            text_parts.append(text)
        elif func_call := part.get("function_call"):
            tool_call: LLMOpenTelemetryToolCall = {
                "id": f"tool_{len(tool_calls)}",
                "type": "function",
                "function": {
                    "name": func_call.get("name") or "",
                    "arguments": json.dumps(func_call.get("args", {})),
                },
            }
            tool_calls.append(tool_call)
        elif blob := part.get("inline_data"):
            if (data := blob.get("data")) and (mime_type := blob.get("mime_type")):
                # Handle both bytes and base64-encoded string
                if isinstance(data, bytes):
                    encoded_data = base64.b64encode(data).decode("utf-8")
                else:
                    # Already base64 encoded string
                    encoded_data = data
                inline_data.append(
                    {
                        "mime_type": mime_type,
                        "data": encoded_data,
                    }
                )

    if text_parts:
        message["content"] = "\n".join(text_parts)
    if tool_calls:
        message["tool_calls"] = tool_calls
    if inline_data:
        message["inline_data"] = inline_data
    return message


def process_response(
    span: Span,
    response: GenerateContentResponse,
) -> None:
    set_response_attributes(span, response)
    process_response_to_events(response, span)


def process_response_to_events(
    response: GenerateContentResponse,
    span: Span,
) -> None:
    for index, candidate in enumerate(response.candidates or []):
        if not (content := candidate.content):
            continue  # pragma: no cover

        message: LLMOpenTelemetryMessage = {
            "role": content.role or "model",
        }

        text_parts: list[str] = []
        tool_calls: list[LLMOpenTelemetryToolCall] = []

        if content.parts:
            for part in content.parts:
                if part.text:
                    text_parts.append(part.text)
                elif part_function_call := part.function_call:
                    function_call: LLMOpenTelemetryFunctionCall = {
                        "name": part_function_call.name or "",
                        "arguments": json.dumps(part_function_call.args)
                        if part_function_call.args
                        else "",
                    }

                    tool_call: LLMOpenTelemetryToolCall = {
                        "id": f"tool_{len(tool_calls)}",
                        "type": "function",
                        "function": function_call,
                    }
                    tool_calls.append(tool_call)

        if text_parts:
            message["content"] = "\n".join(text_parts)

        if tool_calls:
            message["tool_calls"] = tool_calls

        attributes: dict[str, AttributeValue] = {
            "gen_ai.system": "google_genai",
            "gen_ai.choice.index": index,
        }

        if isinstance(candidate.finish_reason, FinishReason):
            attributes["gen_ai.choice.finish_reason"] = candidate.finish_reason.name

        if message.get("content") or message.get("tool_calls"):
            attributes["gen_ai.choice.message"] = json.dumps(message)

        span.add_event("gen_ai.choice", attributes=attributes)
