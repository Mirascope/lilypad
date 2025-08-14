"""Google client instrumentation for OpenTelemetry tracing.

This module provides instrumentation for the Google Python client to automatically
create OpenTelemetry spans for API calls.
"""

from __future__ import annotations

import logging
from importlib.metadata import PackageNotFoundError, version

from opentelemetry.trace import get_tracer
from wrapt import FunctionWrapper

from ._patch import (
    async_generate_content_patch_factory,
    generate_content_patch_factory,
)
from opentelemetry.semconv.schemas import Schemas

from google.genai.models import AsyncModels, Models

logger = logging.getLogger(__name__)


def instrument_google(client: Models | AsyncModels) -> None:
    if hasattr(client, "_lilypad_instrumented"):
        logger.debug("Google GenAI client already instrumented")
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

    module_name = client.__class__.__module__
    class_name = client.__class__.__name__

    if class_name == "Models":
        try:
            client.generate_content = FunctionWrapper(
                client.generate_content,
                generate_content_patch_factory(tracer),
            )
        except AttributeError as e:
            logger.warning(f"Failed to wrap generate_content: {type(e).__name__}")

        # TODO: add support for generate_content_stream after refactoring
    elif class_name == "AsyncModels":
        try:
            client.generate_content = FunctionWrapper(
                client.generate_content,
                async_generate_content_patch_factory(tracer),
            )
        except AttributeError as e:
            logger.warning(f"Failed to wrap generate_content: {type(e).__name__}")

        # TODO: add support for generate_content_stream after refactoring
    else:
        logger.warning(f"Unknown Google GenAI client class: {module_name}.{class_name}")
        return

    client._lilypad_instrumented = True  # pyright: ignore[reportAttributeAccessIssue]
    logger.debug(f"Instrumented Google GenAI client: {module_name}.{class_name}")
