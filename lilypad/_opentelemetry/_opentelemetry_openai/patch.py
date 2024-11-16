# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Modifications copyright (C) 2024 Mirascope
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from opentelemetry.semconv.attributes import error_attributes
from opentelemetry.trace import SpanKind, Status, StatusCode, Tracer

from lilypad._opentelemetry._opentelemetry_openai.utils import (
    OpenAIChunkHandler,
    OpenAIMetadata,
    default_openai_cleanup,
    set_message_event,
    set_response_attributes,
)
from lilypad._opentelemetry._utils import (
    AsyncStreamWrapper,
    StreamWrapper,
    set_server_address_and_port,
)


def get_llm_request_attributes(
    kwargs,
    client_instance,
    operation_name=gen_ai_attributes.GenAiOperationNameValues.CHAT.value,
):
    attributes = {
        gen_ai_attributes.GEN_AI_OPERATION_NAME: operation_name,
        gen_ai_attributes.GEN_AI_SYSTEM: gen_ai_attributes.GenAiSystemValues.OPENAI.value,
        gen_ai_attributes.GEN_AI_REQUEST_MODEL: kwargs.get("model"),
        gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE: kwargs.get("temperature"),
        gen_ai_attributes.GEN_AI_REQUEST_TOP_P: kwargs.get("p") or kwargs.get("top_p"),
        gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS: kwargs.get("max_tokens"),
        gen_ai_attributes.GEN_AI_REQUEST_PRESENCE_PENALTY: kwargs.get(
            "presence_penalty"
        ),
        gen_ai_attributes.GEN_AI_REQUEST_FREQUENCY_PENALTY: kwargs.get(
            "frequency_penalty"
        ),
        gen_ai_attributes.GEN_AI_OPENAI_REQUEST_RESPONSE_FORMAT: kwargs.get(
            "response_format"
        ),
        gen_ai_attributes.GEN_AI_OPENAI_REQUEST_SEED: kwargs.get("seed"),
    }

    set_server_address_and_port(client_instance, attributes)
    service_tier = kwargs.get("service_tier")
    attributes[gen_ai_attributes.GEN_AI_OPENAI_RESPONSE_SERVICE_TIER] = (
        service_tier if service_tier != "auto" else None
    )

    # filter out None values
    return {k: v for k, v in attributes.items() if v is not None}


def chat_completions_create(tracer: Tracer):
    def traced_method(wrapped, instance, args, kwargs):
        span_attributes = {**get_llm_request_attributes(kwargs, instance)}

        span_name = f"{span_attributes[gen_ai_attributes.GEN_AI_OPERATION_NAME]} {span_attributes[gen_ai_attributes.GEN_AI_REQUEST_MODEL]}"
        with tracer.start_as_current_span(
            name=span_name,
            kind=SpanKind.CLIENT,
            attributes=span_attributes,
            end_on_exit=False,
        ) as span:
            if span.is_recording():
                for message in kwargs.get("messages", []):
                    set_message_event(span, message)
            try:
                result = wrapped(*args, **kwargs)
                if kwargs.get("stream", False):
                    return StreamWrapper(
                        span=span,
                        stream=result,
                        metadata=OpenAIMetadata(),
                        chunk_handler=OpenAIChunkHandler(),
                        cleanup_handler=default_openai_cleanup,
                    )

                if span.is_recording():
                    set_response_attributes(span, result)
                span.end()
                return result

            except Exception as error:
                span.set_status(Status(StatusCode.ERROR, str(error)))
                if span.is_recording():
                    span.set_attribute(
                        error_attributes.ERROR_TYPE, type(error).__qualname__
                    )
                span.end()
                raise

    return traced_method


def chat_completions_create_async(tracer: Tracer):
    async def traced_method(wrapped, instance, args, kwargs):
        span_attributes = {**get_llm_request_attributes(kwargs, instance)}

        span_name = f"{span_attributes[gen_ai_attributes.GEN_AI_OPERATION_NAME]} {span_attributes[gen_ai_attributes.GEN_AI_REQUEST_MODEL]}"
        with tracer.start_as_current_span(
            name=span_name,
            kind=SpanKind.CLIENT,
            attributes=span_attributes,
            end_on_exit=False,
        ) as span:
            if span.is_recording():
                for message in kwargs.get("messages", []):
                    set_message_event(span, message)
            try:
                result = await wrapped(*args, **kwargs)
                if kwargs.get("stream", False):
                    return AsyncStreamWrapper(
                        span=span,
                        stream=result,
                        metadata=OpenAIMetadata(),
                        chunk_handler=OpenAIChunkHandler(),
                        cleanup_handler=default_openai_cleanup,
                    )

                if span.is_recording():
                    set_response_attributes(span, result)
                span.end()
                return result

            except Exception as error:
                span.set_status(Status(StatusCode.ERROR, str(error)))
                if span.is_recording():
                    span.set_attribute(
                        error_attributes.ERROR_TYPE, type(error).__qualname__
                    )
                span.end()
                raise

    return traced_method