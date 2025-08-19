"""Mistral client instrumentation for OpenTelemetry tracing.

This module provides instrumentation for the Mistral Python client to automatically
create OpenTelemetry spans for API calls.
"""

import logging
from importlib.metadata import PackageNotFoundError, version

from wrapt import FunctionWrapper
from opentelemetry.trace import get_tracer
from opentelemetry.semconv.schemas import Schemas

from . import _patch

from mistralai import Mistral

logger = logging.getLogger(__name__)


def instrument_mistral(
    client: Mistral,
) -> None:
    """
    Instrument the Mistral client with OpenTelemetry tracing.

    Args:
        client: The Mistral instance to instrument.
    """
    # TODO: Add support for chat.stream and chat.stream_async methods after protocol refactoring
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

    # Wrap synchronous complete method
    try:
        client.chat.complete = FunctionWrapper(
            client.chat.complete,
            _patch.chat_complete_patch_factory(tracer),
        )
        logger.debug("Successfully wrapped Mistral.chat.complete")
    except Exception as e:
        logger.warning(f"Failed to wrap Mistral.chat.complete: {type(e).__name__}: {e}")

    # Wrap asynchronous complete_async method
    try:
        client.chat.complete_async = FunctionWrapper(
            client.chat.complete_async,
            _patch.chat_complete_async_patch_factory(tracer),
        )
        logger.debug("Successfully wrapped Mistral.chat.complete_async")
    except Exception as e:
        logger.warning(
            f"Failed to wrap Mistral.chat.complete_async: {type(e).__name__}: {e}"
        )

    client._lilypad_instrumented = True  # pyright: ignore[reportAttributeAccessIssue]
