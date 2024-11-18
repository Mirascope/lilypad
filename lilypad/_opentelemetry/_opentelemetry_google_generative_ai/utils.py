import base64
import json
from io import BytesIO
from typing import Any, TypedDict

import PIL.WebPImagePlugin
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from opentelemetry.trace import Span
from opentelemetry.util.types import AttributeValue

from lilypad._opentelemetry._utils import (
    ChoiceBuffer,
    set_server_address_and_port,
)


class GeminiMetadata(TypedDict, total=False):
    response_id: str | None
    response_model: str | None
    finish_reasons: list[str]
    prompt_token_count: int | None
    candidates_token_count: int | None


class GeminiChunkHandler:
    def extract_metadata(self, chunk: Any, metadata: GeminiMetadata) -> None:
        if not metadata.get("response_model") and hasattr(chunk, "model"):
            metadata["response_model"] = chunk.model
        if not metadata.get("response_id") and hasattr(chunk, "id"):
            metadata["response_id"] = chunk.id

    def process_chunk(self, chunk: Any, buffers: list[ChoiceBuffer]) -> None:
        if not hasattr(chunk, "candidates"):
            return

        for candidate in chunk.candidates:
            if not candidate.content:
                continue
            part = candidate.content.parts[0]
            # Ensure enough choice buffers
            while len(buffers) <= candidate.index:
                buffers.append(ChoiceBuffer(len(buffers)))

            if part.text is not None:
                buffers[candidate.index].append_text_content(part.text)


def default_gemini_cleanup(
    span: Span, metadata: GeminiMetadata, buffers: list[ChoiceBuffer]
) -> None:
    """Default Gemini cleanup handler"""
    attributes: dict[str, AttributeValue] = {}
    if response_model := metadata.get("response_model"):
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_MODEL] = response_model
    if response_id := metadata.get("response_id"):
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_ID] = response_id
    if finish_reasons := metadata.get("finish_reasons"):
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = finish_reasons

    span.set_attributes(attributes)
    for idx, choice in enumerate(buffers):
        message: dict[str, Any] = {"role": "assistant"}
        if choice.text_content:
            message["content"] = "".join(choice.text_content)

        event_attributes = {
            gen_ai_attributes.GEN_AI_SYSTEM: "gemini",
            "index": idx,
            "finish_reason": choice.finish_reason or "none",
            "message": json.dumps(message),
        }
        span.add_event("gen_ai.choice", attributes=event_attributes)


def get_llm_request_attributes(
    kwargs: dict[str, Any],
    client_instance: Any,
    operation_name: str = gen_ai_attributes.GenAiOperationNameValues.CHAT.value,
) -> dict[str, AttributeValue]:
    attributes = {
        gen_ai_attributes.GEN_AI_OPERATION_NAME: operation_name,
        gen_ai_attributes.GEN_AI_SYSTEM: "gemini",
        gen_ai_attributes.GEN_AI_REQUEST_MODEL: kwargs.get("model")
        or get_gemini_model_name(client_instance),
        gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE: kwargs.get("temperature"),
        gen_ai_attributes.GEN_AI_REQUEST_TOP_P: kwargs.get("p") or kwargs.get("top_p"),
        gen_ai_attributes.GEN_AI_REQUEST_TOP_K: kwargs.get("top_k"),
        gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS: kwargs.get("max_output_tokens"),
        gen_ai_attributes.GEN_AI_REQUEST_STOP_SEQUENCES: kwargs.get("stop_sequences"),
        gen_ai_attributes.GEN_AI_REQUEST_PRESENCE_PENALTY: kwargs.get(
            "presence_penalty"
        ),
        gen_ai_attributes.GEN_AI_REQUEST_FREQUENCY_PENALTY: kwargs.get(
            "frequency_penalty"
        ),
        gen_ai_attributes.GEN_AI_OPENAI_REQUEST_RESPONSE_FORMAT: kwargs.get(
            "response_schema"
        ),
    }

    set_server_address_and_port(client_instance, attributes)
    return {k: v for k, v in attributes.items() if v is not None}


def get_tool_calls(parts: list[Any]) -> list[dict[str, Any]]:
    calls = []
    for part in parts:
        tool_call = part.function_call
        if tool_call:
            tool_call_dict = {"type": "function", "function": {}}

            if name := getattr(tool_call, "name", None):
                tool_call_dict["function"]["name"] = name

                if hasattr(tool_call, "args"):
                    tool_call_dict["function"]["arguments"] = dict(
                        tool_call.args.items()
                    )

            calls.append(tool_call_dict)
    return calls


def set_content_event(span: Span, content: Any) -> None:
    attributes: dict[str, AttributeValue] = {gen_ai_attributes.GEN_AI_SYSTEM: "gemini"}
    role = content.get("role", "")
    parts = content.get("parts")
    content = []
    if role == "user" and parts:
        for part in parts:
            if isinstance(part, dict) and "mime_type" in part and "data" in part:
                # Handle binary data by base64 encoding it
                content.append(
                    {
                        "mime_type": part["mime_type"],
                        "data": base64.b64encode(part["data"]).decode("utf-8"),
                    }
                )
            elif isinstance(part, PIL.WebPImagePlugin.WebPImageFile):
                buffered = BytesIO()
                part.save(
                    buffered, format="WEBP"
                )  # Use "WEBP" to maintain the original format
                img_bytes = buffered.getvalue()
                content.append(
                    {
                        "mime_type": "image/webp",
                        "data": base64.b64encode(img_bytes).decode("utf-8"),
                    }
                )
            else:
                content.append(part)
        attributes["content"] = json.dumps(content)
    elif role == "model" and (tool_calls := get_tool_calls(parts)):
        attributes["tool_calls"] = json.dumps(tool_calls)
    # TODO: Convert to using Otel Events API
    span.add_event(
        f"gen_ai.{role}.message",
        attributes=attributes,
    )


def get_candidate_event(candidate: Any) -> dict[str, AttributeValue]:
    attributes: dict[str, AttributeValue] = {gen_ai_attributes.GEN_AI_SYSTEM: "gemini"}
    if content := candidate.content:
        message_dict = {
            "role": content.role,
        }
        if parts := content.parts:
            message_dict["content"] = [part.text for part in parts]
        if tool_calls := get_tool_calls(parts):
            message_dict["tool_calls"] = tool_calls
        attributes["message"] = json.dumps(message_dict)
        attributes["index"] = candidate.index
        attributes["finish_reason"] = (
            candidate.finish_reason if candidate.finish_reason is not None else "none"
        )
    return attributes


def set_response_attributes(span: Span, response: Any, client_instance: Any) -> None:
    attributes: dict[str, AttributeValue] = {
        gen_ai_attributes.GEN_AI_RESPONSE_MODEL: get_gemini_model_name(client_instance)
    }
    if candidates := getattr(response, "candidates", None):
        finish_reasons = []
        for candidate in candidates:
            choice_attributes = get_candidate_event(candidate)
            span.add_event(
                "gen_ai.choice",
                attributes=choice_attributes,
            )
            finish_reasons.append(int(candidate.finish_reason))
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = finish_reasons
    if id := getattr(response, "id", None):
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_ID] = id
    if usage := getattr(response, "usage_metadata", None):
        attributes[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] = (
            usage.prompt_token_count
        )
        attributes[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] = (
            usage.candidates_token_count
        )

    span.set_attributes(attributes)


def get_gemini_model_name(client_instance: Any) -> str:
    llm_model = "unknown"
    if hasattr(client_instance, "_model_id"):
        llm_model = client_instance._model_id
    if hasattr(client_instance, "_model_name"):
        llm_model = client_instance._model_name
    return llm_model


def set_stream(span: Span, stream: Any, client_instance: Any) -> None:
    attributes: dict[str, AttributeValue] = {
        gen_ai_attributes.GEN_AI_RESPONSE_MODEL: get_gemini_model_name(client_instance)
    }
    finish_reasons = []
    prompt_token_count = 0
    candidates_token_count = 0
    for chunk in stream:
        if candidates := getattr(chunk, "candidates", None):
            for candidate in candidates:
                choice_attributes = get_candidate_event(candidate)
                span.add_event(
                    "gen_ai.choice",
                    attributes=choice_attributes,
                )
                finish_reasons.append(int(candidate.finish_reason))
        if id := getattr(chunk, "id", None):
            attributes[gen_ai_attributes.GEN_AI_RESPONSE_ID] = id
        if usage := getattr(chunk, "usage_metadata", None):
            prompt_token_count += usage.prompt_token_count
            candidates_token_count += usage.candidates_token_count

    attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = finish_reasons
    if prompt_token_count > 0:
        attributes[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] = prompt_token_count
    if candidates_token_count > 0:
        attributes[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] = (
            candidates_token_count
        )
    span.set_attributes(attributes)


async def set_stream_async(span: Span, stream: Any, client_instance: Any) -> None:
    attributes: dict[str, AttributeValue] = {
        gen_ai_attributes.GEN_AI_RESPONSE_MODEL: get_gemini_model_name(client_instance)
    }
    finish_reasons = []
    prompt_token_count = 0
    candidates_token_count = 0
    async for chunk in stream:
        if candidates := getattr(chunk, "candidates", None):
            for candidate in candidates:
                choice_attributes = get_candidate_event(candidate)
                span.add_event(
                    "gen_ai.choice",
                    attributes=choice_attributes,
                )
                finish_reasons.append(int(candidate.finish_reason))
        if id := getattr(chunk, "id", None):
            attributes[gen_ai_attributes.GEN_AI_RESPONSE_ID] = id
        if usage := getattr(chunk, "usage_metadata", None):
            prompt_token_count += usage.prompt_token_count
            candidates_token_count += usage.candidates_token_count

    attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = finish_reasons
    if prompt_token_count > 0:
        attributes[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] = prompt_token_count
    if candidates_token_count > 0:
        attributes[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] = (
            candidates_token_count
        )
    span.set_attributes(attributes)
