from typing import Any

from mypy_boto3_bedrock_runtime.type_defs import ConverseStreamOutputTypeDef
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from opentelemetry.trace import Span
from opentelemetry.util.types import AttributeValue

from lilypad._opentelemetry._utils import ChoiceBuffer


class BedrockMetadata(dict):
    finish_reasons: list[str]
    prompt_tokens: int | None
    completion_tokens: int | None
    response_model: str | None


class BedrockChunkHandler:
    def extract_metadata(self, chunk: ConverseStreamOutputTypeDef, metadata: BedrockMetadata) -> None:
        # TODO: Fix this
        usage = getattr(chunk, "usage_metadata", None)
        if usage:
            if getattr(usage, "prompt_token_count", None) is not None:
                metadata["prompt_tokens"] = usage.prompt_token_count
            if getattr(usage, "candidates_token_count", None) is not None:
                metadata["completion_tokens"] = usage.candidates_token_count

        if hasattr(chunk, "model") and chunk.model:
            metadata["response_model"] = chunk.model
        elif hasattr(chunk, "modelId") and chunk.modelId:
            metadata["response_model"] = chunk.modelId

        # finish_reasons
        if hasattr(chunk, "finish_reasons") and chunk.finish_reasons:
            metadata["finish_reasons"] = chunk.finish_reasons

    def process_chunk(self, chunk: Any, buffers: list[ChoiceBuffer]) -> None:
        candidates = getattr(chunk, "candidates", None)
        if candidates:
            for candidate in candidates:
                while len(buffers) <= candidate.index:
                    buffers.append(ChoiceBuffer(len(buffers)))
                if getattr(candidate, "finish_reason", None):
                    buffers[candidate.index].finish_reason = candidate.finish_reason
                content = getattr(candidate, "content", None)
                if content and hasattr(content, "parts"):
                    for part in content.parts:
                        if "text" in part:
                            buffers[candidate.index].append_text_content(part["text"])
        else:
            output = getattr(chunk, "output", {})
            message = output.get("message", {})
            content_arr = message.get("content", [])
            if not buffers:
                buffers.append(ChoiceBuffer(0))
            for c in content_arr:
                if "text" in c:
                    buffers[0].append_text_content(c["text"])


def default_bedrock_cleanup(span: Span, metadata: BedrockMetadata, buffers: list[ChoiceBuffer]) -> None:
    attributes: dict[str, AttributeValue] = {}
    if response_model := metadata.get("response_model"):
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_MODEL] = response_model
    if finish_reasons := metadata.get("finish_reasons"):
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = finish_reasons
    if prompt_tokens := metadata.get("prompt_tokens"):
        attributes[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] = prompt_tokens
    if completion_tokens := metadata.get("completion_tokens"):
        attributes[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] = completion_tokens

    span.set_attributes(attributes)
    for idx, choice in enumerate(buffers):
        message = {"role": "assistant"}
        if choice.text_content:
            message["content"] = "".join(choice.text_content)
        event_attributes: dict[str, AttributeValue] = {
            gen_ai_attributes.GEN_AI_SYSTEM: "bedrock",
            "index": idx,
            "finish_reason": choice.finish_reason or "none",
            "message": str(message),
        }
        span.add_event("gen_ai.choice", attributes=event_attributes)


def get_bedrock_llm_request_attributes(
    params: dict[str, Any],
    instance: Any = None
) -> dict[str, AttributeValue]:
    attributes: dict[str, AttributeValue] = {
        gen_ai_attributes.GEN_AI_OPERATION_NAME: "chat",
        gen_ai_attributes.GEN_AI_SYSTEM: "bedrock",
    }

    model_id = params.get("modelId")
    if model_id is not None:
        attributes[gen_ai_attributes.GEN_AI_REQUEST_MODEL] = model_id

    return {k: v for k, v in attributes.items() if v is not None}
