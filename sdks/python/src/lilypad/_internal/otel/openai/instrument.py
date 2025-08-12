"""OpenAI client instrumentation for OpenTelemetry tracing.

This module provides instrumentation for the OpenAI Python client to automatically
create OpenTelemetry spans for API calls.
"""

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
# Modifications copyright (C) 2025 Mirascope

import logging
from importlib.metadata import PackageNotFoundError, version

from wrapt import FunctionWrapper, wrap_function_wrapper
from openai import OpenAI, AsyncOpenAI
from opentelemetry.trace import get_tracer
from opentelemetry.semconv.schemas import Schemas

from . import _patch

logger = logging.getLogger(__name__)


def instrument_openai(client: OpenAI | AsyncOpenAI) -> None:
    """
    Instrument the OpenAI client with OpenTelemetry tracing.

    Args:
        client: The OpenAI client instance to instrument.
    """
    if hasattr(client, "_lilypad_instrumented"):
        logger.debug(f"{type(client).__name__} already instrumented, skipping")
        return

    try:
        lilypad_version = version("lilypad-sdk")
    except PackageNotFoundError:
        lilypad_version = "unknown"
        logger.debug("Could not determine lilypad-sdk version")

    tracer = get_tracer(
        __name__,
        lilypad_version,
        schema_url=Schemas.V1_28_0.value,
    )

    if isinstance(client, AsyncOpenAI):
        try:
            wrap_function_wrapper(
                module="openai.resources.chat.completions",
                name="AsyncCompletions.create",
                wrapper=_patch.chat_completions_create_async_patch_factory(tracer),
            )
            client.chat.completions.create = FunctionWrapper(
                client.chat.completions.create,
                _patch.chat_completions_create_async_patch_factory(tracer),
            )
            logger.debug("Successfully wrapped AsyncCompletions.create")
        except Exception as e:
            logger.warning(
                f"Failed to wrap AsyncCompletions.create: {type(e).__name__}: {e}"
            )

        try:
            client.chat.completions.parse = FunctionWrapper(
                client.chat.completions.parse,
                _patch.chat_completions_parse_async_patch_factory(tracer),
            )
            logger.debug("Successfully wrapped AsyncCompletions.parse")
        except Exception as e:
            logger.warning(
                f"Failed to wrap AsyncCompletions.parse: {type(e).__name__}: {e}"
            )

    else:
        try:
            client.chat.completions.create = FunctionWrapper(
                client.chat.completions.create,
                _patch.chat_completions_create_patch_factory(tracer),
            )
            logger.debug("Successfully wrapped Completions.create")
        except Exception as e:
            logger.warning(
                f"Failed to wrap Completions.create: {type(e).__name__}: {e}"
            )

        try:
            client.chat.completions.parse = FunctionWrapper(
                client.chat.completions.parse,
                _patch.chat_completions_parse_patch_factory(tracer),
            )
            logger.debug("Successfully wrapped Completions.parse")
        except Exception as e:
            logger.warning(f"Failed to wrap Completions.parse: {type(e).__name__}: {e}")

    client._lilypad_instrumented = True  # pyright: ignore[reportAttributeAccessIssue]
