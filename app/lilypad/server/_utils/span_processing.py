"""Shared utilities for span processing across API and queue processor."""

import logging
from typing import Any, cast
from uuid import UUID

from mirascope.core import Provider
from mirascope.core.base.types import CostMetadata
from mirascope.core.costs import calculate_cost
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from ..models.spans import Scope
from ..schemas.span_more_details import calculate_openrouter_cost
from ..schemas.spans import SpanCreate

logger = logging.getLogger(__name__)


def _convert_system_to_provider(system: str) -> Provider:
    """Convert system name to provider name for cost calculation."""
    if system == "az.ai.inference":
        return "azure"
    elif system == "google_genai":
        return "google"
    return cast(Provider, system)


async def create_span_from_data(
    span_data: dict[str, Any],
    child_costs: float = 0,
    child_input_tokens: int | float = 0,
    child_output_tokens: int | float = 0,
) -> SpanCreate:
    """Create a SpanCreate object from span data with proper cost calculation.

    Args:
        span_data: Raw span data dictionary
        child_costs: Sum of costs from child spans (for LILYPAD scope)
        child_input_tokens: Sum of input tokens from child spans (for LILYPAD scope)
        child_output_tokens: Sum of output tokens from child spans (for LILYPAD scope)

    Returns:
        SpanCreate object with calculated costs and tokens
    """
    attributes = span_data.get("attributes", {})

    # Determine scope based on instrumentation scope
    instrumentation_scope = span_data.get("instrumentation_scope", {})
    if instrumentation_scope.get("name") == "lilypad":
        scope = Scope.LILYPAD
        span_cost = child_costs
        input_tokens = int(child_input_tokens) if child_input_tokens else None
        output_tokens = int(child_output_tokens) if child_output_tokens else None
    else:
        scope = Scope.LLM
        span_cost = 0
        input_tokens = attributes.get(gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS)
        output_tokens = attributes.get(gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS)

        # Calculate cost for LLM spans
        if (system := attributes.get(gen_ai_attributes.GEN_AI_SYSTEM)) and (
            model := attributes.get(gen_ai_attributes.GEN_AI_RESPONSE_MODEL)
        ):
            if system == "openrouter":
                cost = await calculate_openrouter_cost(
                    input_tokens, output_tokens, model
                )
            else:
                cost_metadata = CostMetadata(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
                cost = calculate_cost(
                    _convert_system_to_provider(system), model, metadata=cost_metadata
                )
            if cost is not None:
                span_cost = cost

    # Extract function UUID
    function_uuid_str = attributes.get("lilypad.function.uuid")

    # Calculate duration - handles both queue processor and API formats
    duration_ms = span_data.get("duration_ms", 0)
    if duration_ms == 0 and "end_time" in span_data and "start_time" in span_data:
        duration_ms = span_data["end_time"] - span_data["start_time"]

    return SpanCreate(
        span_id=span_data["span_id"],
        type=attributes.get("lilypad.type"),
        function_uuid=UUID(function_uuid_str) if function_uuid_str else None,
        scope=scope,
        data=span_data,
        parent_span_id=span_data.get("parent_span_id"),
        cost=span_cost,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        duration_ms=duration_ms,
    )


def create_span_from_data_sync(
    span_data: dict[str, Any],
    child_costs: float = 0,
    child_input_tokens: int | float = 0,
    child_output_tokens: int | float = 0,
) -> SpanCreate:
    """Create a SpanCreate object from span data (synchronous version).

    This function uses the same logic as create_span_from_data but avoids
    async operations for use in synchronous contexts like thread pools.

    Args:
        span_data: Raw span data dictionary
        child_costs: Sum of costs from child spans (for LILYPAD scope)
        child_input_tokens: Sum of input tokens from child spans (for LILYPAD scope)
        child_output_tokens: Sum of output tokens from child spans (for LILYPAD scope)

    Returns:
        SpanCreate object with calculated costs and tokens
    """
    attributes = span_data.get("attributes", {})

    # Determine scope based on instrumentation scope
    instrumentation_scope = span_data.get("instrumentation_scope", {})
    if instrumentation_scope.get("name") == "lilypad":
        scope = Scope.LILYPAD
        span_cost = child_costs
        input_tokens = int(child_input_tokens) if child_input_tokens else None
        output_tokens = int(child_output_tokens) if child_output_tokens else None
    else:
        scope = Scope.LLM
        span_cost = 0
        input_tokens = attributes.get(gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS)
        output_tokens = attributes.get(gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS)

        # Calculate cost for LLM spans (sync version - no openrouter async call)
        if (system := attributes.get(gen_ai_attributes.GEN_AI_SYSTEM)) and (
            model := attributes.get(gen_ai_attributes.GEN_AI_RESPONSE_MODEL)
        ):
            if system == "openrouter":
                # For sync processing, use pre-calculated cost if available
                # since async openrouter calculation is not available
                span_cost = span_data.get("cost", 0)
            else:
                cost_metadata = CostMetadata(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
                cost = calculate_cost(
                    _convert_system_to_provider(system), model, metadata=cost_metadata
                )
                if cost is not None:
                    span_cost = cost

    # Extract function UUID
    function_uuid_str = attributes.get("lilypad.function.uuid")

    # Calculate duration - handles both queue processor and API formats
    duration_ms = span_data.get("duration_ms", 0)
    if duration_ms == 0 and "end_time" in span_data and "start_time" in span_data:
        duration_ms = span_data["end_time"] - span_data["start_time"]

    return SpanCreate(
        span_id=span_data["span_id"],
        type=attributes.get("lilypad.type"),
        function_uuid=UUID(function_uuid_str) if function_uuid_str else None,
        scope=scope,
        data=span_data,
        parent_span_id=span_data.get("parent_span_id"),
        cost=span_cost,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        duration_ms=duration_ms,
    )
