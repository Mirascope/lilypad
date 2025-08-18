"""Azure AI Inference client instrumentation for OpenTelemetry tracing.

This module provides instrumentation for the Azure AI Inference Python client to automatically
create OpenTelemetry spans for API calls.
"""

import logging
from importlib.metadata import PackageNotFoundError, version

from wrapt import FunctionWrapper
from opentelemetry.trace import get_tracer
from opentelemetry.semconv.schemas import Schemas

from . import _patch


from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.aio import ChatCompletionsClient as AsyncChatCompletionsClient

logger = logging.getLogger(__name__)


# TODO: see if we can refactor this with other providers in a way that makes sense
def instrument_azure(
    client: ChatCompletionsClient | AsyncChatCompletionsClient,
) -> None:
    """
    Instrument the Azure AI Inference client with OpenTelemetry tracing.

    Args:
        client: The Azure ChatCompletionsClient instance to instrument.
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

    if isinstance(client, AsyncChatCompletionsClient):
        try:
            client.complete = FunctionWrapper(
                client.complete,
                _patch.chat_completions_complete_async_patch_factory(tracer),
            )
            logger.debug("Successfully wrapped AsyncChatCompletionsClient.complete")
        except Exception as e:
            logger.warning(
                f"Failed to wrap AsyncChatCompletionsClient.complete: {type(e).__name__}: {e}"
            )
    else:
        try:
            client.complete = FunctionWrapper(
                client.complete,
                _patch.chat_completions_complete_patch_factory(tracer),
            )
            logger.debug("Successfully wrapped ChatCompletionsClient.complete")
        except Exception as e:
            logger.warning(
                f"Failed to wrap ChatCompletionsClient.complete: {type(e).__name__}: {e}"
            )

    client._lilypad_instrumented = True  # pyright: ignore[reportAttributeAccessIssue]
