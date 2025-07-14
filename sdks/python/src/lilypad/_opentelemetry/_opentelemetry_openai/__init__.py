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

import logging
from typing import Any
from collections.abc import Collection

from wrapt import wrap_function_wrapper
from opentelemetry.trace import get_tracer
from opentelemetry.semconv.schemas import Schemas
from opentelemetry.instrumentation.utils import unwrap
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor

from .patch import (
    chat_completions_parse,
    chat_completions_create,
    chat_completions_parse_async,
    chat_completions_create_async,
)

logger = logging.getLogger(__name__)


class OpenAIInstrumentor(BaseInstrumentor):
    def instrumentation_dependencies(self) -> Collection[str]:
        return ("openai>=1.6.0,<2",)

    def _wrap_parse_methods(self, tracer: Any) -> None:
        """Wrap parse methods with version compatibility handling."""
        sync_wrapped = False
        async_wrapped = False

        # Try non-beta location first (OpenAI >= 1.92.0)
        try:
            wrap_function_wrapper(
                module="openai.resources.chat.completions",
                name="Completions.parse",
                wrapper=chat_completions_parse(tracer),
            )
            sync_wrapped = True
            logger.debug("Successfully wrapped Completions.parse at non-beta location")
        except Exception as e:
            logger.debug(f"Failed to wrap Completions.parse at non-beta location: {type(e).__name__}: {e}")

        try:
            wrap_function_wrapper(
                module="openai.resources.chat.completions",
                name="AsyncCompletions.parse",
                wrapper=chat_completions_parse_async(tracer),
            )
            async_wrapped = True
            logger.debug("Successfully wrapped AsyncCompletions.parse at non-beta location")
        except Exception as e:
            logger.debug(f"Failed to wrap AsyncCompletions.parse at non-beta location: {type(e).__name__}: {e}")

        # Try beta location if needed (OpenAI < 1.92.0)
        if not sync_wrapped:
            try:
                wrap_function_wrapper(
                    module="openai.resources.beta.chat.completions",
                    name="Completions.parse",
                    wrapper=chat_completions_parse(tracer),
                )
                sync_wrapped = True
                logger.debug("Successfully wrapped Completions.parse at beta location")
            except Exception as e:
                logger.debug(f"Failed to wrap Completions.parse at beta location: {type(e).__name__}: {e}")

        if not async_wrapped:
            try:
                wrap_function_wrapper(
                    module="openai.resources.beta.chat.completions",
                    name="AsyncCompletions.parse",
                    wrapper=chat_completions_parse_async(tracer),
                )
                async_wrapped = True
                logger.debug("Successfully wrapped AsyncCompletions.parse at beta location")
            except Exception as e:
                logger.debug(f"Failed to wrap AsyncCompletions.parse at beta location: {type(e).__name__}: {e}")

        # Log warning if any parse method failed to wrap
        if not sync_wrapped or not async_wrapped:
            # Try to get OpenAI version for better error context
            version_info = ""
            try:
                import openai

                version_info = f" (OpenAI SDK version: {openai.__version__})"
            except Exception:
                pass

            failed_methods = []
            if not sync_wrapped:
                failed_methods.append("Completions.parse")
            if not async_wrapped:
                failed_methods.append("AsyncCompletions.parse")

            logger.warning(
                f"Failed to instrument OpenAI parse methods: {', '.join(failed_methods)}{version_info}. "
                f"This may be due to OpenAI SDK version incompatibility."
            )

    def _instrument(self, **kwargs: Any) -> None:
        """Enable OpenAI instrumentation."""
        tracer_provider = kwargs.get("tracer_provider")
        tracer = get_tracer(
            __name__,
            "0.1.0",  # Lilypad version
            tracer_provider,
            schema_url=Schemas.V1_28_0.value,
        )

        # Wrap create methods (these haven't moved)
        try:
            wrap_function_wrapper(
                module="openai.resources.chat.completions",
                name="Completions.create",
                wrapper=chat_completions_create(tracer),
            )
            logger.debug("Successfully wrapped Completions.create")
        except Exception as e:
            logger.warning(f"Failed to wrap Completions.create: {type(e).__name__}: {e}")

        try:
            wrap_function_wrapper(
                module="openai.resources.chat.completions",
                name="AsyncCompletions.create",
                wrapper=chat_completions_create_async(tracer),
            )
            logger.debug("Successfully wrapped AsyncCompletions.create")
        except Exception as e:
            logger.warning(f"Failed to wrap AsyncCompletions.create: {type(e).__name__}: {e}")

        # Wrap parse methods with version compatibility
        self._wrap_parse_methods(tracer)

    def _uninstrument(self, **kwargs: Any) -> None:
        """Disable OpenAI instrumentation."""
        try:
            import openai
        except ImportError:
            logger.warning("OpenAI module not found during uninstrumentation")
            return

        # Define unwrap targets
        unwrap_targets = [
            # Create methods (non-beta)
            ("resources.chat.completions.Completions", "create"),
            ("resources.chat.completions.AsyncCompletions", "create"),
            # Parse methods (non-beta, OpenAI >= 1.92.0)
            ("resources.chat.completions.Completions", "parse"),
            ("resources.chat.completions.AsyncCompletions", "parse"),
            # Parse methods (beta, OpenAI < 1.92.0)
            ("resources.beta.chat.completions.Completions", "parse"),
            ("resources.beta.chat.completions.AsyncCompletions", "parse"),
        ]

        # Attempt to unwrap each target
        for attr_path, method_name in unwrap_targets:
            try:
                # Navigate through the attribute path
                target = openai
                for attr in attr_path.split("."):
                    target = getattr(target, attr)

                # Check if the method exists and is wrapped
                if hasattr(target, method_name):
                    unwrap(target, method_name)
                    logger.debug(f"Successfully unwrapped {attr_path}.{method_name}")
            except Exception as e:
                # Log at debug level since missing methods are expected
                logger.debug(f"Failed to unwrap {attr_path}.{method_name}: {type(e).__name__}: {e}")
