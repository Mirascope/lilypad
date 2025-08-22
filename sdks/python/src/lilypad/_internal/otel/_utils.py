"""Utility classes and functions for Lilypad OpenTelemetry instrumentation."""

import base64
import logging
from typing import Any, Protocol, Sequence, cast, runtime_checkable

from opentelemetry.util.types import AttributeValue

from ..utils import json_dumps

logger = logging.getLogger(__name__)


@runtime_checkable
class _InstrumentedClient(Protocol):
    """Protocol for clients that have been instrumented for telemetry."""

    __lilypad_instrumented_client__: bool


def client_is_already_instrumented(client: Any) -> bool:
    """Returns whether a client has already been instrumented."""
    if (
        isinstance(client, _InstrumentedClient)
        and client.__lilypad_instrumented_client__
    ):
        logger.debug(f"{type(client).__name__} has already been instrumented, skipping")
        return True
    return False


def mark_client_as_instrumented(client: Any) -> None:
    """Marks a client as already instrumented for telemetry."""
    cast(_InstrumentedClient, client).__lilypad_instrumented_client__ = True


def serialize_attribute_value(value: Any) -> AttributeValue | None:
    """Returns a serialized attribute value suitable for OpenTelemetry."""
    if value is None:
        return None

    if isinstance(value, str | bool | int | float):
        return value

    if isinstance(value, bytes):  # pragma: no cover
        return base64.b64encode(value).decode("utf-8")

    if isinstance(value, Sequence):  # pragma: no cover
        if not value:
            return []

        first_item = value[0]
        if (
            (
                isinstance(first_item, str)
                and all(isinstance(item, str) for item in value)
            )
            or (
                isinstance(first_item, bool)
                and all(isinstance(item, bool) for item in value)
            )
            or (
                isinstance(first_item, int)
                and all(isinstance(item, int) for item in value)
            )
        ):
            return list(value)
        elif isinstance(first_item, int | float) and all(
            isinstance(item, int | float) for item in value
        ):
            return [float(item) for item in value]
        else:
            # Heterogeneous sequence - serialize each item as a JSON string
            return json_dumps(value)

    # Any other type - serialize as JSON string
    return json_dumps(value)
