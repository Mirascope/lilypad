"""Kafka service for span message handling."""

import json
from typing import Annotated, Any

from fastapi import Depends

from lilypad.server._utils import get_current_user
from lilypad.server.schemas.users import UserPublic
from lilypad.server.settings import get_settings

from .kafka_base import BaseKafkaService


class SpanKafkaService(BaseKafkaService):
    """Kafka service for publishing span messages."""

    def __init__(self, user: UserPublic) -> None:
        """Initialize with user context.
        
        Args:
            user: The authenticated user
        """
        self.user = user
        self._settings = get_settings()

    @property
    def topic(self) -> str:
        """The Kafka topic for span ingestion."""
        return self._settings.kafka_topic_span_ingestion

    def get_key(self, data: dict[str, Any]) -> str | None:
        """Extract trace_id as the partition key."""
        return data.get("trace_id")

    def transform_message(self, data: dict[str, Any]) -> dict[str, Any]:
        """Add user_id to the span data with validation."""
        # Validate required fields first
        if not isinstance(data, dict):
            raise ValueError("Span data must be a dictionary")
        
        # Ensure trace_id is present
        if not data.get("trace_id"):
            raise ValueError("Missing required field: trace_id")
        
        # Validate string lengths for common fields
        max_string_length = 10000  # 10KB per string field
        for _key, value in data.items():
            if isinstance(value, str) and len(value) > max_string_length:
                # Don't include user input in error message
                raise ValueError(f"String field exceeds maximum length of {max_string_length} characters")
        
        # Safely get user_id
        if not self.user:
            raise ValueError("User context is missing")
        
        try:
            user_id = str(self.user.uuid)
        except (AttributeError, TypeError):
            raise ValueError("Invalid user object - missing uuid attribute")
        
        # Create final message
        final_message = {**data, "user_id": user_id}
        
        # Validate final message size using actual JSON encoding
        try:
            # Use the same serialization logic as Kafka producer
            json_bytes = json.dumps(final_message, default=str, check_circular=True).encode("utf-8")
            actual_size = len(json_bytes)
            
            if actual_size > 1048576:  # 1MB
                raise ValueError(f"Message too large: {actual_size} bytes (max 1MB)")
        except (TypeError, ValueError) as e:
            if "circular" in str(e).lower():
                raise ValueError("Message contains circular references")
            raise ValueError("Invalid message data structure")
        
        return final_message


# Dependency injection helper
async def get_span_kafka_service(
    user: Annotated[UserPublic, Depends(get_current_user)]
) -> SpanKafkaService:
    """Get SpanKafkaService instance with dependency injection.
    
    Args:
        user: Current authenticated user from dependency injection
        
    Returns:
        SpanKafkaService instance
    """
    return SpanKafkaService(user)