"""Anthropic client instrumentation for OpenTelemetry tracing.

This module provides instrumentation for the Anthropic Python client to automatically
create OpenTelemetry spans for API calls.
"""

import logging
from importlib.metadata import PackageNotFoundError, version

from wrapt import FunctionWrapper
from anthropic import Anthropic, AsyncAnthropic
from opentelemetry.trace import get_tracer
from opentelemetry.semconv.schemas import Schemas

from . import _patch
from ._patch import (
    messages_stream_patch_factory,
    messages_stream_async_patch_factory,
)

logger = logging.getLogger(__name__)


# TODO: see if we can refactor this with other providers in a way that makes sense
def instrument_anthropic(client: Anthropic | AsyncAnthropic) -> None:
    """
    Instrument the Anthropic client with OpenTelemetry tracing.

    Args:
        client: The Anthropic client instance to instrument.
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

    if isinstance(client, AsyncAnthropic):
        try:
            client.messages.create = FunctionWrapper(
                client.messages.create,
                _patch.messages_create_async_patch_factory(tracer),
            )
            logger.debug("Successfully wrapped AsyncMessages.create")
        except Exception as e:
            logger.warning(
                f"Failed to wrap AsyncMessages.create: {type(e).__name__}: {e}"
            )

        try:
            client.messages.stream = FunctionWrapper(
                client.messages.stream,
                messages_stream_async_patch_factory(tracer),
            )
            logger.debug("Successfully wrapped AsyncMessages.stream")
        except Exception as e:
            logger.warning(
                f"Failed to wrap AsyncMessages.stream: {type(e).__name__}: {e}"
            )

    else:
        try:
            client.messages.create = FunctionWrapper(
                client.messages.create,
                _patch.messages_create_patch_factory(tracer),
            )
            logger.debug("Successfully wrapped Messages.create")
        except Exception as e:
            logger.warning(f"Failed to wrap Messages.create: {type(e).__name__}: {e}")

        try:
            client.messages.stream = FunctionWrapper(
                client.messages.stream,
                messages_stream_patch_factory(tracer),
            )
            logger.debug("Successfully wrapped Messages.stream")
        except Exception as e:
            logger.warning(f"Failed to wrap Messages.stream: {type(e).__name__}: {e}")

    client._lilypad_instrumented = True  # pyright: ignore[reportAttributeAccessIssue]
