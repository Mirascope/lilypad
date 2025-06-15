"""Tests for the Stripe Kafka Service."""

import json
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from lilypad.server.schemas.users import UserPublic
from lilypad.server.services.stripe_kafka_service import (
    StripeKafkaService,
    get_stripe_kafka_service,
)
from lilypad.server.settings import Settings


class TestStripeKafkaService:
    """Test StripeKafkaService class."""

    @pytest.fixture
    def mock_user(self):
        """Create mock user for testing."""
        user = Mock(spec=UserPublic)
        user.uuid = uuid4()
        return user

    @pytest.fixture
    def service(self, mock_user):
        """Create StripeKafkaService instance for testing."""
        with patch("lilypad.server.services.stripe_kafka_service.get_settings") as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_settings.kafka_topic_stripe_ingestion = "stripe-ingestion"
            mock_get_settings.return_value = mock_settings
            
            return StripeKafkaService(mock_user)

    def test_init(self, mock_user):
        """Test StripeKafkaService initialization."""
        with patch("lilypad.server.services.stripe_kafka_service.get_settings") as mock_get_settings:
            mock_settings = Mock(spec=Settings)
            mock_get_settings.return_value = mock_settings
            
            service = StripeKafkaService(mock_user)
            
            assert service.user == mock_user
            assert service._settings == mock_settings

    def test_topic_property(self, service):
        """Test topic property returns correct topic name."""
        assert service.topic == "stripe-ingestion"

    def test_get_key_with_trace_id(self, service):
        """Test get_key returns trace_id when present."""
        data = {"trace_id": "test-trace-123", "other_data": "value"}
        
        result = service.get_key(data)
        
        assert result == "test-trace-123"

    def test_get_key_without_trace_id(self, service):
        """Test get_key returns None when trace_id is missing."""
        data = {"other_data": "value"}
        
        result = service.get_key(data)
        
        assert result is None

    def test_get_key_with_empty_trace_id(self, service):
        """Test get_key returns empty string when trace_id is empty."""
        data = {"trace_id": "", "other_data": "value"}
        
        result = service.get_key(data)
        
        assert result == ""

    def test_transform_message_valid_data(self, service):
        """Test transform_message with valid data."""
        data = {
            "trace_id": "test-trace-123",
            "organization_uuid": str(uuid4()),
            "span_count": 5,
        }
        
        result = service.transform_message(data)
        
        assert result["trace_id"] == "test-trace-123"
        assert result["organization_uuid"] == data["organization_uuid"]
        assert result["span_count"] == 5
        assert result["user_uuid"] == str(service.user.uuid)

    def test_transform_message_non_dict_input(self, service):
        """Test transform_message raises error for non-dict input."""
        with pytest.raises(ValueError, match="stripe data must be a dictionary"):
            service.transform_message("not a dict")

    def test_transform_message_missing_trace_id(self, service):
        """Test transform_message raises error when trace_id is missing."""
        data = {"organization_uuid": str(uuid4())}
        
        with pytest.raises(ValueError, match="Missing required field: trace_id"):
            service.transform_message(data)

    def test_transform_message_empty_trace_id(self, service):
        """Test transform_message raises error when trace_id is empty."""
        data = {"trace_id": "", "organization_uuid": str(uuid4())}
        
        with pytest.raises(ValueError, match="Missing required field: trace_id"):
            service.transform_message(data)

    def test_transform_message_string_too_long(self, service):
        """Test transform_message raises error when string field is too long."""
        data = {
            "trace_id": "test-trace-123",
            "large_field": "x" * 10001,  # Exceeds 10KB limit
        }
        
        with pytest.raises(ValueError, match="String field exceeds maximum length"):
            service.transform_message(data)

    def test_transform_message_no_user(self):
        """Test transform_message raises error when user is None."""
        with patch("lilypad.server.services.stripe_kafka_service.get_settings"):
            service = StripeKafkaService(None)
            data = {"trace_id": "test-trace-123"}
            
            with pytest.raises(ValueError, match="User context is missing"):
                service.transform_message(data)

    def test_transform_message_invalid_user(self):
        """Test transform_message raises error when user has no uuid."""
        mock_user = Mock()
        del mock_user.uuid  # Remove uuid attribute
        
        with patch("lilypad.server.services.stripe_kafka_service.get_settings"):
            service = StripeKafkaService(mock_user)
            data = {"trace_id": "test-trace-123"}
            
            with pytest.raises(ValueError, match="Invalid user object - missing uuid attribute"):
                service.transform_message(data)

    def test_transform_message_user_uuid_none(self):
        """Test transform_message handles user with None uuid."""
        mock_user = Mock()
        mock_user.uuid = None
        
        with patch("lilypad.server.services.stripe_kafka_service.get_settings"):
            service = StripeKafkaService(mock_user)
            data = {"trace_id": "test-trace-123"}
            
            # Should work since str(None) = "None"
            result = service.transform_message(data)
            assert result["user_uuid"] == "None"

    def test_transform_message_non_serializable_data(self, service):
        """Test transform_message handles non-serializable data with default=str."""
        class NonSerializable:
            def __str__(self):
                return "non_serializable_object"
        
        data = {
            "trace_id": "test-trace-123",
            "bad_field": NonSerializable(),
        }
        
        # Should work because default=str makes it JSON serializable during validation
        # but the original object is preserved in the result
        result = service.transform_message(data)
        assert isinstance(result["bad_field"], NonSerializable)
        assert str(result["bad_field"]) == "non_serializable_object"

    def test_transform_message_circular_reference(self, service):
        """Test transform_message raises error for circular references."""
        data = {"trace_id": "test-trace-123"}
        data["self_ref"] = data  # Create circular reference
        
        with pytest.raises(ValueError, match="Circular reference detected"):
            service.transform_message(data)

    def test_transform_message_size_validation(self, service):
        """Test transform_message validates message size."""
        # Create a large but valid message (under 1MB)
        large_data = "x" * 5000  # 5KB string
        data = {
            "trace_id": "test-trace-123",
            "field1": large_data,
            "field2": large_data,
            # Total should be under 1MB
        }
        
        result = service.transform_message(data)
        assert "user_uuid" in result

    def test_transform_message_string_field_too_large(self, service):
        """Test transform_message raises error when string field is too large."""
        # Create a string field that exceeds the 10KB limit
        large_data = "x" * 10001  # Exceeds 10KB limit
        data = {
            "trace_id": "test-trace-123",
            "large_field": large_data,
        }
        
        with pytest.raises(ValueError, match="String field exceeds maximum length"):
            service.transform_message(data)

    def test_transform_message_estimated_size_too_large(self, service):
        """Test transform_message raises error when estimated message size is too large."""
        # Create many medium-sized fields that together exceed 1MB estimated size
        # Each field is under 10KB individually but together they're too large
        medium_data = "x" * 5000  # 5KB each
        data = {
            "trace_id": "test-trace-123",
        }
        
        # Add many fields to exceed 1MB estimate
        for i in range(200):  # 200 * 5KB = 1MB + overhead
            data[f"field_{i}"] = medium_data
        
        with pytest.raises(ValueError, match="Message too large"):
            service.transform_message(data)

    def test_transform_message_truly_non_serializable(self, service):
        """Test transform_message raises error for data that can't be converted to string."""
        class BadObject:
            def __str__(self):
                raise RuntimeError("Can't convert to string")
        
        data = {
            "trace_id": "test-trace-123",
            "bad_field": BadObject(),
        }
        
        # The actual exception is RuntimeError, but it's raised during JSON validation
        with pytest.raises(RuntimeError, match="Can't convert to string"):
            service.transform_message(data)

    def test_transform_message_type_error_non_serializable(self, service):
        """Test transform_message handles TypeError from JSON serialization."""
        # Create object that causes TypeError during JSON encoding
        class BadObject:
            def __str__(self):
                return "valid_string"
            
            def __repr__(self):
                # This shouldn't be called, but just in case
                return "BadObject()"
        
        # Patch json.dumps to raise TypeError to test the exception handling
        import json
        from unittest.mock import patch
        
        data = {
            "trace_id": "test-trace-123",
            "bad_field": BadObject(),
        }
        
        with patch('json.dumps', side_effect=TypeError("Object not JSON serializable")):
            with pytest.raises(ValueError, match="Message contains non-serializable data types"):
                service.transform_message(data)

    def test_transform_message_circular_reference_specific_message(self, service):
        """Test transform_message handles ValueError with 'circular' in message."""
        # Test the specific condition in the code that checks for 'circular' in the error message
        import json
        from unittest.mock import patch
        
        data = {
            "trace_id": "test-trace-123",
            "field": "value",
        }
        
        # Create a ValueError with 'circular' in the message to trigger line 92
        with patch('json.dumps', side_effect=ValueError("detected circular reference in data")):
            with pytest.raises(ValueError, match="Message contains circular references"):
                service.transform_message(data)

    def test_transform_message_preserves_original_data(self, service):
        """Test transform_message doesn't modify original data."""
        original_data = {
            "trace_id": "test-trace-123",
            "span_count": 5,
        }
        data_copy = original_data.copy()
        
        result = service.transform_message(data_copy)
        
        # Original should be unchanged
        assert original_data == {"trace_id": "test-trace-123", "span_count": 5}
        # Result should have additional user_uuid
        assert result["user_uuid"] == str(service.user.uuid)
        assert result["trace_id"] == "test-trace-123"
        assert result["span_count"] == 5

    def test_transform_message_json_serializable_result(self, service):
        """Test transform_message result is JSON serializable."""
        data = {
            "trace_id": "test-trace-123",
            "number": 42,
            "boolean": True,
            "null_value": None,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
        }
        
        result = service.transform_message(data)
        
        # Should be able to serialize to JSON
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
        
        # Should be able to deserialize back
        deserialized = json.loads(json_str)
        assert deserialized["trace_id"] == "test-trace-123"


@pytest.mark.asyncio
async def test_get_stripe_kafka_service_with_kafka():
    """Test get_stripe_kafka_service returns service when Kafka is configured."""
    mock_settings = Mock(spec=Settings)
    mock_settings.kafka_bootstrap_servers = "localhost:9092"
    mock_settings.kafka_topic_stripe_ingestion = "stripe-ingestion"
    mock_settings.stripe_api_key = "sk_test_123"
    
    mock_user = Mock(spec=UserPublic)
    mock_user.uuid = uuid4()
    
    result = await get_stripe_kafka_service(mock_settings, mock_user)
    
    assert isinstance(result, StripeKafkaService)
    assert result.user == mock_user


@pytest.mark.asyncio
async def test_get_stripe_kafka_service_without_kafka():
    """Test get_stripe_kafka_service returns None when Kafka is not configured."""
    mock_settings = Mock(spec=Settings)
    mock_settings.kafka_bootstrap_servers = None
    
    mock_user = Mock(spec=UserPublic)
    
    result = await get_stripe_kafka_service(mock_settings, mock_user)
    
    assert result is None


@pytest.mark.asyncio
async def test_get_stripe_kafka_service_empty_kafka_servers():
    """Test get_stripe_kafka_service returns None when Kafka servers string is empty."""
    mock_settings = Mock(spec=Settings)
    mock_settings.kafka_bootstrap_servers = ""
    
    mock_user = Mock(spec=UserPublic)
    
    result = await get_stripe_kafka_service(mock_settings, mock_user)
    
    assert result is None