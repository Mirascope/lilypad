from typing import Any

from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from opentelemetry.util.types import AttributeValue


def get_llm_request_attributes(
    kwargs: dict[str, Any], instance: Any
) -> dict[str, AttributeValue]:
    """Extracts common request attributes from kwargs and instance.

    Sets default operation name, system, and model name.
    Also extracts generation parameters if provided.
    """
    attributes: dict[str, AttributeValue] = {
        gen_ai_attributes.GEN_AI_OPERATION_NAME: "generate_content",
        gen_ai_attributes.GEN_AI_SYSTEM: "google_genai",
        gen_ai_attributes.GEN_AI_REQUEST_MODEL: getattr(
            instance, "_model_name", "unknown"
        ),
    }
    generation_config = kwargs.get("config")
    if generation_config and isinstance(generation_config, dict):
        if (temp := generation_config.get("temperature")) is not None:
            attributes[gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE] = temp
        if (top_p := generation_config.get("top_p")) is not None:
            attributes[gen_ai_attributes.GEN_AI_REQUEST_TOP_P] = top_p
        if (top_k := generation_config.get("top_k")) is not None:
            attributes[gen_ai_attributes.GEN_AI_REQUEST_TOP_K] = top_k
        if (max_tokens := generation_config.get("max_output_tokens")) is not None:
            attributes[gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS] = max_tokens
    if kwargs.get("stream", False):
        attributes["google_genai.stream"] = True
    return {k: v for k, v in attributes.items() if v is not None}


def set_content_event(span: Any, content: Any) -> None:
    """Records an event for each content element in the request."""
    span.add_event("gen_ai.content", attributes={"content": str(content)})


def set_response_attributes(span: Any, response: Any, instance: Any) -> None:
    """Records response attributes on the span.

    Iterates over response candidates and records candidate events.
    """
    response_attrs = {
        gen_ai_attributes.GEN_AI_RESPONSE_MODEL: getattr(
            instance, "_model_name", "unknown"
        )
    }
    finish_reasons = []
    candidates = getattr(response, "candidates", None)
    if candidates:
        for candidate in candidates:
            event_attrs = {
                "candidate_index": candidate.index,
                "finish_reason": candidate.finish_reason,
            }
            span.add_event("gen_ai.candidate", attributes=event_attrs)
            finish_reasons.append(candidate.finish_reason)
    if finish_reasons:
        response_attrs[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = (
            finish_reasons
        )
    span.set_attributes(response_attrs)


def set_stream(span: Any, stream: Any, instance: Any) -> None:
    """Processes a synchronous streaming response.

    Iterates over stream chunks, recording candidate events on the span.
    """
    stream_attrs = {
        gen_ai_attributes.GEN_AI_RESPONSE_MODEL: getattr(
            instance, "_model_name", "unknown"
        )
    }
    finish_reasons = []
    for chunk in stream:
        candidates = getattr(chunk, "candidates", None)
        if candidates:
            for candidate in candidates:
                event_attrs = {
                    "candidate_index": candidate.index,
                    "finish_reason": candidate.finish_reason,
                }
                span.add_event("gen_ai.candidate", attributes=event_attrs)
                finish_reasons.append(candidate.finish_reason)
    if finish_reasons:
        stream_attrs[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = finish_reasons
    span.set_attributes(stream_attrs)


async def set_stream_async(span: Any, stream: Any, instance: Any) -> None:
    """Processes an asynchronous streaming response.

    Asynchronously iterates over stream chunks and records candidate events on the span.
    (Note: This function fully consumes the stream.)
    """
    finish_reasons = []
    async for chunk in stream:
        candidates = getattr(chunk, "candidates", None)
        if candidates:
            for candidate in candidates:
                event_attrs = {
                    "candidate_index": candidate.index,
                    "finish_reason": candidate.finish_reason,
                }
                span.add_event("gen_ai.candidate", attributes=event_attrs)
                finish_reasons.append(candidate.finish_reason)
    if finish_reasons:
        span.set_attributes(
            {gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS: finish_reasons}
        )
