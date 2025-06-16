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


@pytest.fixture
def stripe_kafka_user():
    """Create mock user for Stripe Kafka testing."""
    user = Mock(spec=UserPublic)
    user.uuid = uuid4()
    return user


@pytest.fixture
def stripe_kafka_service(stripe_kafka_user):
    """Create StripeKafkaService instance for testing."""
    with patch("lilypad.server.services.stripe_kafka_service.get_settings") as mock_get_settings:
        mock_settings = Mock(spec=Settings)
        mock_settings.kafka_topic_stripe_ingestion = "stripe-ingestion"
        mock_get_settings.return_value = mock_settings
        
        return StripeKafkaService(stripe_kafka_user)


# ===== Initialization Tests =====

def test_stripe_kafka_service_init(stripe_kafka_user):
    """Test StripeKafkaService initialization."""
    with patch("lilypad.server.services.stripe_kafka_service.get_settings") as mock_get_settings:
        mock_settings = Mock(spec=Settings)
        mock_get_settings.return_value = mock_settings
        
        service = StripeKafkaService(stripe_kafka_user)
        
        assert service.user == stripe_kafka_user
        assert service._settings == mock_settings


def test_topic_property(stripe_kafka_service):
    """Test topic property returns correct topic name."""
    assert stripe_kafka_service.topic == "stripe-ingestion"


# ===== Parameterized Tests for get_key =====

@pytest.mark.parametrize("data,expected_key", [
    ({"trace_id": "test-trace-123"}, "test-trace-123"),
    ({"trace_id": ""}, ""),
    ({"other_data": "value"}, None),
    ({}, None),
])
def test_get_key(stripe_kafka_service, data, expected_key):
    """Test get_key with various data inputs."""
    result = stripe_kafka_service.get_key(data)
    assert result == expected_key


# ===== Valid Message Transformation Tests =====

def test_transform_message_valid_data(stripe_kafka_service):
    """Test transform_message with valid data."""
    data = {
        "trace_id": "test-trace-123",
        "organization_uuid": str(uuid4()),
        "span_count": 5,
    }
    
    result = stripe_kafka_service.transform_message(data)
    
    assert result["trace_id"] == "test-trace-123"
    assert result["organization_uuid"] == data["organization_uuid"]
    assert result["span_count"] == 5
    assert result["user_uuid"] == str(stripe_kafka_service.user.uuid)


# ===== Parameterized Error Tests =====

@pytest.mark.parametrize("invalid_data,error_match", [
    ("not a dict", "stripe data must be a dictionary"),
    ({"organization_uuid": str(uuid4())}, "Missing required field: trace_id"),
    ({"trace_id": "", "organization_uuid": str(uuid4())}, "Missing required field: trace_id"),
    ({"trace_id": "test", "large_field": "x" * 10001}, "String field exceeds maximum length"),
])
def test_transform_message_errors(stripe_kafka_service, invalid_data, error_match):
    """Test transform_message error cases."""
    with pytest.raises(ValueError, match=error_match):
        stripe_kafka_service.transform_message(invalid_data)


# ===== User Context Tests =====

@pytest.mark.parametrize("user_setup,expected_error", [
    (None, "User context is missing"),
    ({"missing_uuid": True}, "Invalid user object - missing uuid attribute"),
])
def test_transform_message_user_errors(user_setup, expected_error):
    """Test transform_message with various user context errors."""
    if user_setup is None:
        mock_user = None
    else:
        mock_user = Mock()
        if user_setup.get("missing_uuid"):
            del mock_user.uuid
    
    with patch("lilypad.server.services.stripe_kafka_service.get_settings"):
        service = StripeKafkaService(mock_user)
        data = {"trace_id": "test-trace-123"}
        
        with pytest.raises(ValueError, match=expected_error):
            service.transform_message(data)


def test_transform_message_user_uuid_none():
    """Test transform_message handles user with None uuid."""
    mock_user = Mock()
    mock_user.uuid = None
    
    with patch("lilypad.server.services.stripe_kafka_service.get_settings"):
        service = StripeKafkaService(mock_user)
        data = {"trace_id": "test-trace-123"}
        
        # Should work since str(None) = "None"
        result = service.transform_message(data)
        assert result["user_uuid"] == "None"


# ===== JSON Serialization Tests =====

def test_transform_message_non_serializable_data(stripe_kafka_service):
    """Test transform_message handles non-serializable data with default=str."""
    class NonSerializable:
        def __str__(self):
            return "non_serializable_object"
    
    data = {
        "trace_id": "test-trace-123",
        "bad_field": NonSerializable(),
    }
    
    # Should work because default=str makes it JSON serializable during validation
    result = stripe_kafka_service.transform_message(data)
    assert isinstance(result["bad_field"], NonSerializable)
    assert str(result["bad_field"]) == "non_serializable_object"


def test_transform_message_circular_reference(stripe_kafka_service):
    """Test transform_message raises error for circular references."""
    data = {"trace_id": "test-trace-123"}
    data["self_ref"] = data  # Create circular reference
    
    with pytest.raises(ValueError, match="Circular reference detected"):
        stripe_kafka_service.transform_message(data)


# ===== Size Validation Tests =====

@pytest.mark.parametrize("field_count,field_size,should_pass", [
    (1, 5000, True),   # Single 5KB field - OK
    (200, 5000, False), # 200 * 5KB = 1MB+ - Too large
    (1, 10001, False),  # Single field > 10KB - Too large
])
def test_transform_message_size_validation(stripe_kafka_service, field_count, field_size, should_pass):
    """Test transform_message size validation."""
    data = {"trace_id": "test-trace-123"}
    
    # Add fields based on parameters
    for i in range(field_count):
        data[f"field_{i}"] = "x" * field_size
    
    if should_pass:
        result = stripe_kafka_service.transform_message(data)
        assert "user_uuid" in result
    else:
        expected_error = "String field exceeds maximum length" if field_size > 10000 else "Message too large"
        with pytest.raises(ValueError, match=expected_error):
            stripe_kafka_service.transform_message(data)


# ===== Special Error Cases =====

def test_transform_message_truly_non_serializable(stripe_kafka_service):
    """Test transform_message raises error for data that can't be converted to string."""
    class BadObject:
        def __str__(self):
            raise RuntimeError("Can't convert to string")
    
    data = {
        "trace_id": "test-trace-123",
        "bad_field": BadObject(),
    }
    
    with pytest.raises(RuntimeError, match="Can't convert to string"):
        stripe_kafka_service.transform_message(data)


@pytest.mark.parametrize("error_type,error_message,expected_match", [
    (TypeError, "Object not JSON serializable", "Message contains non-serializable data types"),
    (ValueError, "detected circular reference in data", "Message contains circular references"),
])
def test_transform_message_json_errors(stripe_kafka_service, error_type, error_message, expected_match):
    """Test transform_message handles various JSON serialization errors."""
    data = {
        "trace_id": "test-trace-123",
        "field": "value",
    }
    
    with patch("json.dumps", side_effect=error_type(error_message)):
        with pytest.raises(ValueError, match=expected_match):
            stripe_kafka_service.transform_message(data)


# ===== Data Integrity Tests =====

def test_transform_message_preserves_original_data(stripe_kafka_service):
    """Test transform_message doesn't modify original data."""
    original_data = {
        "trace_id": "test-trace-123",
        "span_count": 5,
    }
    data_copy = original_data.copy()
    
    result = stripe_kafka_service.transform_message(data_copy)
    
    # Original should be unchanged
    assert original_data == {"trace_id": "test-trace-123", "span_count": 5}
    # Result should have additional user_uuid
    assert result["user_uuid"] == str(stripe_kafka_service.user.uuid)
    assert result["trace_id"] == "test-trace-123"
    assert result["span_count"] == 5


def test_transform_message_json_serializable_result(stripe_kafka_service):
    """Test transform_message result is JSON serializable."""
    data = {
        "trace_id": "test-trace-123",
        "number": 42,
        "boolean": True,
        "null_value": None,
        "list": [1, 2, 3],
        "nested": {"key": "value"},
    }
    
    result = stripe_kafka_service.transform_message(data)
    
    # Should be able to serialize to JSON
    json_str = json.dumps(result)
    assert isinstance(json_str, str)
    
    # Should be able to deserialize back
    deserialized = json.loads(json_str)
    assert deserialized["trace_id"] == "test-trace-123"


# ===== get_stripe_kafka_service Tests =====

@pytest.mark.parametrize("kafka_servers,expected_result", [
    ("localhost:9092", True),  # Kafka configured
    (None, False),             # No Kafka servers
    ("", False),               # Empty Kafka servers
])
@pytest.mark.asyncio
async def test_get_stripe_kafka_service(kafka_servers, expected_result, stripe_kafka_user):
    """Test get_stripe_kafka_service with various configurations."""
    mock_settings = Mock(spec=Settings)
    mock_settings.kafka_bootstrap_servers = kafka_servers
    mock_settings.kafka_topic_stripe_ingestion = "stripe-ingestion"
    mock_settings.stripe_api_key = "sk_test_123"
    
    result = await get_stripe_kafka_service(mock_settings, stripe_kafka_user)
    
    if expected_result:
        assert isinstance(result, StripeKafkaService)
        assert result.user == stripe_kafka_user
    else:
        assert result is None