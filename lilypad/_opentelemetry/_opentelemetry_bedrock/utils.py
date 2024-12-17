from typing import Any

from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from opentelemetry.trace import Span


def get_bedrock_llm_request_attributes(params: dict[str, Any]) -> dict[str, Any]:
    attributes = {
        gen_ai_attributes.GEN_AI_OPERATION_NAME: "chat",
        gen_ai_attributes.GEN_AI_SYSTEM: "bedrock",
    }

    model_id = params.get("modelId")
    if model_id:
        attributes[gen_ai_attributes.GEN_AI_REQUEST_MODEL] = model_id

    inference_config = params.get("inferenceConfig", {})
    max_tokens = inference_config.get("maxTokens")
    temperature = inference_config.get("temperature")
    top_p = inference_config.get("topP")
    stop_sequences = inference_config.get("stopSequences")

    if temperature is not None:
        attributes[gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE] = temperature
    if top_p is not None:
        attributes[gen_ai_attributes.GEN_AI_REQUEST_TOP_P] = top_p
    if max_tokens is not None:
        attributes[gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS] = max_tokens
    if stop_sequences:
        attributes[gen_ai_attributes.GEN_AI_REQUEST_STOP_SEQUENCES] = stop_sequences

    return {k: v for k, v in attributes.items() if v is not None}


def set_bedrock_response_attributes(span: Span, response: Any) -> None:
    attributes = {}

    usage = response.get("usage", {})
    input_tokens = usage.get("inputTokens")
    output_tokens = usage.get("outputTokens")
    if input_tokens is not None:
        attributes[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] = input_tokens
    if output_tokens is not None:
        attributes[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] = output_tokens

    stop_reason = response.get("stopReason")
    if stop_reason:
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = [stop_reason]

    message = response.get("output", {}).get("message", {})
    content_parts = message.get("content", [])
    text_content = []
    for c in content_parts:
        if "text" in c:
            text_content.append(c["text"])
    choice_attributes = {
        gen_ai_attributes.GEN_AI_SYSTEM: "bedrock",
        "message": str({"role": "assistant", "content": text_content}),
        "index": 0,
        "finish_reason": stop_reason if stop_reason else "none",
    }
    span.add_event("gen_ai.choice", attributes=choice_attributes)

    span.set_attributes(attributes)
