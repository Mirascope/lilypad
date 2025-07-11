"""Kafka service for stripe message handling."""

import json
from typing import Annotated, Any

from fastapi import Depends

from lilypad.server._utils import get_current_user
from lilypad.server.schemas.users import UserPublic
from lilypad.server.settings import Settings, get_settings

from .kafka_base import BaseKafkaService


class StripeKafkaService(BaseKafkaService):
    """Kafka service for publishing stripe messages."""

    def __init__(
        self,
        user: Annotated[UserPublic, Depends(get_current_user)],
    ) -> None:
        """Initialize with user context.

        Args:
            user: The authenticated user
        """
        self.user = user
        self._settings = get_settings()

    @property
    def topic(self) -> str:
        """The Kafka topic for stripe ingestion."""
        return self._settings.kafka_topic_stripe_ingestion

    def get_key(self, data: dict[str, Any]) -> str | None:
        """Extract trace_id as the partition key."""
        return data.get("trace_id")

    def transform_message(self, data: dict[str, Any]) -> dict[str, Any]:
        """Add user_id to the stripe data with validation."""
        # Validate required fields first
        if not isinstance(data, dict):
            raise ValueError("stripe data must be a dictionary")
        # Ensure trace_id is present
        if not data.get("trace_id"):
            raise ValueError("Missing required field: trace_id")
        # Validate string lengths for common fields
        max_string_length = 10000  # 10KB per string field
        for _key, value in data.items():
            if isinstance(value, str) and len(value) > max_string_length:
                # Don't include user input in error message
                raise ValueError(
                    f"String field exceeds maximum length of {max_string_length} characters"
                )
        # Safely get user_id
        if not self.user:
            raise ValueError("User context is missing")
        try:
            user_uuid = str(self.user.uuid)
        except (AttributeError, TypeError):
            raise ValueError("Invalid user object - missing uuid attribute")
        # Create final message
        final_message = {**data, "user_uuid": user_uuid}

        # Validate message structure and estimate size
        try:
            # Quick structure validation (will catch circular references)
            json.dumps(final_message, default=str, check_circular=True)

            # Estimate size without full encoding (avoid double serialization)
            # Rough estimate: JSON adds ~20% overhead for quotes, commas, etc.
            estimated_size = (
                sum(
                    len(str(k)) + len(str(v)) + 6  # 6 bytes for ": " and ", "
                    for k, v in final_message.items()
                )
                + 2
            )  # {} brackets

            # Add buffer for JSON encoding overhead
            estimated_size = int(estimated_size * 1.3)

            if estimated_size > 1048576:  # 1MB
                raise ValueError(
                    f"Message too large: estimated {estimated_size} bytes (max 1MB)"
                )
        except TypeError as e:
            raise ValueError("Message contains non-serializable data types") from e
        except ValueError as e:
            # Re-raise ValueError with more specific message
            if isinstance(e.args[0], str) and "circular" in e.args[0]:
                raise ValueError("Message contains circular references") from e
            raise

        return final_message


# Dependency injection helper
async def get_stripe_kafka_service(
    settings: Annotated[Settings, Depends(get_settings)],
    user: Annotated[UserPublic, Depends(get_current_user)],
) -> StripeKafkaService | None:
    """Get StripeKafkaService instance with dependency injection.

    Args:
        settings: Application settings from dependency injection
        user: Current authenticated user from dependency injection

    Returns:
        StripeKafkaService instance
    """
    is_stripe_kafka_enabled = (
        settings.kafka_bootstrap_servers
        and settings.kafka_topic_stripe_ingestion
        and settings.stripe_api_key
    )
    return StripeKafkaService(user) if is_stripe_kafka_enabled else None
