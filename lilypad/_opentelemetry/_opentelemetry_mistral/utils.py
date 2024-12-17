from typing import Any

from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from opentelemetry.trace import Span


def get_mistral_llm_request_attributes(kwargs: dict[str, Any]) -> dict[str, Any]:
    # mistralai client.chat.complete arguments:
    # model, messages, temperature, top_p, max_tokens, ...
    attributes: dict[str, Any] = {
        gen_ai_attributes.GEN_AI_OPERATION_NAME: "chat",
        gen_ai_attributes.GEN_AI_SYSTEM: "mistral",
    }

    model = kwargs.get("model")
    if model:
        attributes[gen_ai_attributes.GEN_AI_REQUEST_MODEL] = model

    temperature = kwargs.get("temperature")
    if temperature is not None:
        attributes[gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE] = temperature

    top_p = kwargs.get("top_p")
    if top_p is not None:
        attributes[gen_ai_attributes.GEN_AI_REQUEST_TOP_P] = top_p

    max_tokens = kwargs.get("max_tokens")
    if max_tokens is not None:
        attributes[gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS] = max_tokens

    # stop sequences
    stop = kwargs.get("stop")
    if stop is not None:
        # stop can be a string or list[str], unify to list
        if isinstance(stop, list):
            attributes[gen_ai_attributes.GEN_AI_REQUEST_STOP_SEQUENCES] = stop
        else:
            attributes[gen_ai_attributes.GEN_AI_REQUEST_STOP_SEQUENCES] = [stop]

    return {k: v for k, v in attributes.items() if v is not None}


def set_mistral_response_attributes(span: Span, response: Any) -> None:
    attributes = {
        gen_ai_attributes.GEN_AI_RESPONSE_MODEL: response.model
        if hasattr(response, "model")
        else "<unknown>"
    }

    # response is ChatCompletionResponse with usage and choices
    usage = getattr(response, "usage", None)
    if usage:
        prompt_tokens = getattr(usage, "prompt_tokens", None)
        completion_tokens = getattr(usage, "completion_tokens", None)
        if prompt_tokens is not None:
            attributes[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] = prompt_tokens
        if completion_tokens is not None:
            attributes[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] = completion_tokens

    # finish reasons are inside choices
    finish_reasons = []
    if hasattr(response, "choices") and response.choices:
        for idx, choice in enumerate(response.choices):
            choice_event_attrs = {
                gen_ai_attributes.GEN_AI_SYSTEM: "mistral",
                "index": idx,
            }
            # Each choice has a message with content
            # and possibly a finish_reason?
            # According to Mistral model, ChatCompletionResponse.choices[i].finish_reason might exist.
            finish_reason = getattr(choice, "finish_reason", None)
            if finish_reason:
                finish_reasons.append(finish_reason)
                choice_event_attrs["finish_reason"] = finish_reason
            else:
                choice_event_attrs["finish_reason"] = "none"

            # message content
            message = getattr(choice.message, "content", "")
            choice_event_attrs["message"] = str(
                {"role": "assistant", "content": message}
            )
            span.add_event("gen_ai.choice", attributes=choice_event_attrs)

    if finish_reasons:
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = finish_reasons

    span.set_attributes(attributes)
