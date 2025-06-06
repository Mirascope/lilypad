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
        # Validate message size (limit to 1MB)
        try:
            message_size = len(json.dumps(data))
            if message_size > 1048576:  # 1MB
                raise ValueError(f"Message too large: {message_size} bytes (max 1MB)")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid message data: {e}")
        
        # Validate required fields
        if not isinstance(data, dict):
            raise ValueError("Span data must be a dictionary")
        
        # Validate string lengths for common fields
        max_string_length = 10000  # 10KB per string field
        for key, value in data.items():
            if isinstance(value, str) and len(value) > max_string_length:
                raise ValueError(f"Field '{key}' too long: {len(value)} chars (max {max_string_length})")
        
        # Ensure trace_id is present if we're using it as key
        if self.get_key(data) is None and "trace_id" not in data:
            raise ValueError("Missing required field: trace_id")
        
        return {**data, "user_id": str(self.user.uuid)}


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