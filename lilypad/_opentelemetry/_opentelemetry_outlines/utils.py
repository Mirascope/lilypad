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
from __future__ import annotations

import json
from typing import Any

from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from opentelemetry.trace import Span


def record_prompts(span: Span, prompts: str | list[str]) -> None:
    """Record user prompts as events on the span."""
    if not span.is_recording():
        return
    if isinstance(prompts, str):
        span.add_event("gen_ai.user.message", attributes={"content": prompts})
    else:
        for p in prompts:
            span.add_event("gen_ai.user.message", attributes={"content": p})


def record_stop_sequences(span: Span, stop_at: str | list[str] | None) -> None:
    """Record stop sequences as an attribute on the span."""
    if not span.is_recording() or not stop_at:
        return
    stops = stop_at if isinstance(stop_at, list) else [stop_at]
    # stops is now list[str]
    span.set_attribute("outlines.request.stop_sequences", json.dumps(stops))


def set_response_event(span: Span, result: Any) -> None:
    """Record the final response as an event."""
    # Consider truncation if `result` is very large
    if span.is_recording():
        span.add_event("gen_ai.response", attributes={"response": str(result)})


def extract_generation_attributes(
    generation_parameters: Any,
    sampling_parameters: Any,
    system_name: str,
    model_name: str,
) -> dict[str, Any]:
    """Extract common attributes from generation/sampling parameters."""
    attributes: dict[str, Any] = {
        gen_ai_attributes.GEN_AI_SYSTEM: system_name,
        gen_ai_attributes.GEN_AI_OPERATION_NAME: "generate",
        gen_ai_attributes.GEN_AI_REQUEST_MODEL: model_name,
    }

    if generation_parameters:
        max_tokens = generation_parameters.max_tokens
        seed = generation_parameters.seed
        if max_tokens is not None:
            attributes[gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS] = max_tokens
        if seed is not None:
            attributes["outlines.request.seed"] = seed

    if sampling_parameters:
        # sampling_parameters: (sampler, num_samples, top_p, top_k, temperature)
        top_p = sampling_parameters.top_p
        temperature = sampling_parameters.temperature
        if top_p is not None:
            attributes[gen_ai_attributes.GEN_AI_REQUEST_TOP_P] = top_p
        if temperature is not None:
            attributes[gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE] = temperature

    return attributes
