from typing import Any

from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from opentelemetry.trace import Span


def get_vertex_model_name(instance: Any) -> str:
    # Attempt to extract model name from instance of GenerativeModel.
    llm_model = "unknown"
    if hasattr(instance, "_model_name") and instance._model_name:
        llm_model = instance._model_name
    return llm_model


def get_vertex_llm_request_attributes(
    kwargs: dict[str, Any], instance: Any
) -> dict[str, Any]:
    attributes: dict[str, Any] = {
        gen_ai_attributes.GEN_AI_OPERATION_NAME: "chat",
        gen_ai_attributes.GEN_AI_SYSTEM: gen_ai_attributes.GenAiSystemValues.VERTEX_AI,
        gen_ai_attributes.GEN_AI_REQUEST_MODEL: get_vertex_model_name(instance),
    }

    generation_config = kwargs.get("generation_config")
    if generation_config:
        temp = None
        top_p = None
        top_k = None
        max_tokens = None
        freq_pen = None
        pres_pen = None
        if hasattr(generation_config, "_raw_generation_config"):
            cfg = generation_config._raw_generation_config
            temp = cfg.temperature
            top_p = cfg.top_p
            top_k = cfg.top_k
            max_tokens = cfg.max_output_tokens
            freq_pen = cfg.frequency_penalty
            pres_pen = cfg.presence_penalty
        elif isinstance(generation_config, dict):
            temp = generation_config.get("temperature")
            top_p = generation_config.get("top_p")
            top_k = generation_config.get("top_k")
            max_tokens = generation_config.get("max_output_tokens")
            freq_pen = generation_config.get("frequency_penalty")
            pres_pen = generation_config.get("presence_penalty")

        if temp is not None:
            attributes[gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE] = temp
        if top_p is not None:
            attributes[gen_ai_attributes.GEN_AI_REQUEST_TOP_P] = top_p
        if top_k is not None:
            attributes[gen_ai_attributes.GEN_AI_REQUEST_TOP_K] = top_k
        if max_tokens is not None:
            attributes[gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS] = max_tokens
        if pres_pen is not None:
            attributes[gen_ai_attributes.GEN_AI_REQUEST_PRESENCE_PENALTY] = pres_pen
        if freq_pen is not None:
            attributes[gen_ai_attributes.GEN_AI_REQUEST_FREQUENCY_PENALTY] = freq_pen

        # Stop sequences
        if _raw_generation_config := getattr(
            generation_config, "_raw_generation_config", None
        ):
            stop_seqs = _raw_generation_config.stop_sequences  # pyright: ignore [reportAttributeAccessIssue]
            if stop_seqs:
                attributes[gen_ai_attributes.GEN_AI_REQUEST_STOP_SEQUENCES] = stop_seqs

    stream = kwargs.get("stream", False)
    if stream:
        attributes["vertex.stream"] = True

    return {k: v for k, v in attributes.items() if v is not None}


def get_vertex_candidate_event(candidate: Any) -> dict[str, Any]:
    attributes: dict[str, Any] = {
        gen_ai_attributes.GEN_AI_SYSTEM: gen_ai_attributes.GenAiSystemValues.VERTEX_AI
    }
    message_dict = {
        "role": candidate.content.role if candidate.content else "assistant",
    }
    if candidate.content and candidate.content.parts:
        text_parts = []
        for p in candidate.content.parts:
            if hasattr(p, "text") and p.text is not None:
                text_parts.append(p.text)
        message_dict["content"] = text_parts

        if hasattr(candidate, "function_calls"):
            fcalls = candidate.function_calls
            if fcalls:
                tool_calls = []
                for fc in fcalls:
                    tool_calls.append(
                        {
                            "type": "function",
                            "function": {
                                "name": fc.name,
                                "arguments": fc.args if fc.args else {},
                            },
                        }
                    )
                message_dict["tool_calls"] = tool_calls

    attributes["message"] = str(message_dict)
    attributes["index"] = candidate.index
    attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = (
        int(candidate.finish_reason) if candidate.finish_reason is not None else "none"
    )
    return attributes


def set_vertex_response_attributes(span: Span, response: Any, instance: Any) -> None:
    attributes: dict[str, Any] = {
        gen_ai_attributes.GEN_AI_RESPONSE_MODEL: get_vertex_model_name(instance)
    }

    candidates = getattr(response, "candidates", None)
    finish_reasons = []
    if candidates:
        for candidate in candidates:
            choice_attrs = get_vertex_candidate_event(candidate)
            span.add_event("gen_ai.choice", attributes=choice_attrs)
            finish_reasons.append(int(candidate.finish_reason))
    if finish_reasons:
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = finish_reasons

    usage = getattr(response, "usage_metadata", None)
    if usage:
        pt = usage.prompt_token_count
        ct = usage.candidates_token_count
        if pt is not None:
            attributes[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] = pt
        if ct is not None:
            attributes[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] = ct

    span.set_attributes(attributes)


def set_vertex_stream(span: Span, stream: Any, instance: Any) -> None:
    attributes: dict[str, Any] = {
        gen_ai_attributes.GEN_AI_RESPONSE_MODEL: get_vertex_model_name(instance)
    }
    finish_reasons = []
    prompt_token_count = 0
    candidates_token_count = 0
    for chunk in stream:
        if candidates := getattr(chunk, "candidates", None):
            for candidate in candidates:
                choice_attributes = get_vertex_candidate_event(candidate)
                span.add_event("gen_ai.choice", attributes=choice_attributes)
                finish_reasons.append(int(candidate.finish_reason))
        if usage := getattr(chunk, "usage_metadata", None):
            if usage.prompt_token_count:
                prompt_token_count += usage.prompt_token_count
            if usage.candidates_token_count:
                candidates_token_count += usage.candidates_token_count

    attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = finish_reasons
    if prompt_token_count > 0:
        attributes[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] = prompt_token_count
    if candidates_token_count > 0:
        attributes[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] = (
            candidates_token_count
        )
    span.set_attributes(attributes)


async def set_vertex_stream_async(span: Span, stream: Any, instance: Any) -> None:
    attributes: dict[str, Any] = {
        gen_ai_attributes.GEN_AI_RESPONSE_MODEL: get_vertex_model_name(instance)
    }
    finish_reasons = []
    prompt_token_count = 0
    candidates_token_count = 0
    async for chunk in stream:
        if candidates := getattr(chunk, "candidates", None):
            for candidate in candidates:
                choice_attributes = get_vertex_candidate_event(candidate)
                span.add_event("gen_ai.choice", attributes=choice_attributes)
                finish_reasons.append(int(candidate.finish_reason))
        if usage := getattr(chunk, "usage_metadata", None):
            if usage.prompt_token_count:
                prompt_token_count += usage.prompt_token_count
            if usage.candidates_token_count:
                candidates_token_count += usage.candidates_token_count

    attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = finish_reasons
    if prompt_token_count > 0:
        attributes[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] = prompt_token_count
    if candidates_token_count > 0:
        attributes[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] = (
            candidates_token_count
        )
    span.set_attributes(attributes)
