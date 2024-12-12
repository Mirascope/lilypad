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

from collections.abc import Awaitable, Callable, Generator
from functools import wraps
from typing import Any

from opentelemetry.trace import SpanKind, Status, StatusCode
from typing_extensions import ParamSpec

from .utils import (
    extract_generation_attributes,
    record_prompts,
    record_stop_sequences,
    set_response_event,
)

P = ParamSpec("P")


def model_generate(tracer: Any) -> Callable[[Callable[P, Any]], Callable[P, Any]]:
    """Wrapper for synchronous generate methods."""

    def decorator(wrapped: Callable[P, Any]) -> Callable[P, Any]:
        @wraps(wrapped)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            self = args[0]
            prompts: str | list[str] = args[1]
            generation_parameters: Any = args[2]
            _ = args[3]  # logits_processor
            sampling_parameters: Any = args[4]

            model_name = (
                getattr(self, "model_name", None)
                or getattr(self, "model", None).__class__.__name__
            )
            attributes = extract_generation_attributes(
                generation_parameters, sampling_parameters, "outlines", model_name
            )
            span_name = f"outlines.generate {model_name}"

            with tracer.start_as_current_span(
                name=span_name,
                kind=SpanKind.CLIENT,
                attributes=attributes,
                end_on_exit=False,
            ) as span:
                stop_at = (
                    generation_parameters.stop_at if generation_parameters else None
                )
                record_prompts(span, prompts)
                record_stop_sequences(span, stop_at)

                try:
                    result = wrapped(*args, **kwargs)
                    set_response_event(span, result)
                    span.end()
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    span.end()
                    raise

        return wrapper

    return decorator


def model_generate_stream(
    tracer: Any,
) -> Callable[[Callable[P, Any]], Callable[P, Any]]:
    """Wrapper for synchronous stream methods."""

    def decorator(wrapped: Callable[P, Any]) -> Callable[P, Any]:
        @wraps(wrapped)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            self = args[0]
            prompts: str | list[str] = args[1]
            generation_parameters: Any = kwargs.get("generation_parameters")
            sampling_parameters: Any = kwargs.get("sampling_parameters")

            model_name = (
                getattr(self, "model_name", None)
                or getattr(self, "model", None).__class__.__name__
            )
            attributes = extract_generation_attributes(
                generation_parameters, sampling_parameters, "outlines", model_name
            )
            span_name = f"outlines.stream {model_name}"

            with tracer.start_as_current_span(
                name=span_name,
                kind=SpanKind.CLIENT,
                attributes=attributes,
                end_on_exit=False,
            ) as span:
                stop_at = (
                    generation_parameters.stop_at if generation_parameters else None
                )
                record_prompts(span, prompts)
                record_stop_sequences(span, stop_at)

                try:
                    generator = wrapped(*args, **kwargs)

                    def gen() -> Generator[Any, None, None]:
                        try:
                            for chunk in generator:
                                if span.is_recording():
                                    span.add_event(
                                        "gen_ai.partial_response",
                                        attributes={"chunk": str(chunk)},
                                    )
                                yield chunk
                        except Exception as e:
                            span.set_status(Status(StatusCode.ERROR, str(e)))
                            span.record_exception(e)
                            raise
                        finally:
                            span.end()

                    return gen()
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    span.end()
                    raise

        return wrapper

    return decorator


def model_generate_async(
    tracer: Any,
) -> Callable[[Callable[P, Awaitable[Any]]], Callable[P, Awaitable[Any]]]:
    """Wrapper for async methods like async def generate_chat(...)"""

    def decorator(wrapped: Callable[P, Awaitable[Any]]) -> Callable[P, Awaitable[Any]]:
        @wraps(wrapped)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            self = args[0]
            prompts: str | list[str] = args[1]
            generation_parameters: Any = args[2]
            _ = args[3]  # logits_processor
            sampling_parameters: Any = args[4]

            model_name = (
                getattr(self, "model_name", None)
                or getattr(self, "model", None).__class__.__name__
            )
            attributes = extract_generation_attributes(
                generation_parameters, sampling_parameters, "outlines", model_name
            )
            span_name = f"outlines.generate_async {model_name}"

            with tracer.start_as_current_span(
                name=span_name,
                kind=SpanKind.CLIENT,
                attributes=attributes,
                end_on_exit=False,
            ) as span:
                stop_at = (
                    generation_parameters.stop_at if generation_parameters else None
                )
                record_prompts(span, prompts)
                record_stop_sequences(span, stop_at)

                try:
                    result = await wrapped(*args, **kwargs)
                    set_response_event(span, result)
                    span.end()
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    span.end()
                    raise

        return wrapper

    return decorator
