"""Tests for user consents API endpoints."""

from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from lilypad.server.models.user_consents import UserConsentTable


def test_post_user_consent_success(client: TestClient):
    """Test successful user consent creation."""
    consent_data = {
        "privacy_policy_version": "2025-04-04",
        "tos_version": "2025-04-04"
    }
    
    response = client.post("/user-consents", json=consent_data)
    
    assert response.status_code == 200
    created_consent = response.json()
    assert created_consent["privacy_policy_version"] == "2025-04-04"
    assert created_consent["tos_version"] == "2025-04-04"
    assert "uuid" in created_consent
    assert "privacy_policy_accepted_at" in created_consent
    assert "tos_accepted_at" in created_consent


def test_post_user_consent_no_auth():
    """Test user consent creation without authentication."""
    # Create client without auth overrides
    from lilypad.server.api.v0.main import api
    from fastapi.testclient import TestClient
    
    client_no_auth = TestClient(api)
    
    consent_data = {
        "privacy_policy_version": "2025-04-04",
        "tos_version": "2025-04-04"
    }
    
    response = client_no_auth.post("/user-consents", json=consent_data)
    
    assert response.status_code == 401


def test_post_user_consent_invalid_data(client: TestClient):
    """Test user consent creation with invalid data."""
    # Missing required fields
    consent_data = {
        "privacy_policy_version": "2025-04-04"
        # Missing tos_version
    }
    
    response = client.post("/user-consents", json=consent_data)
    
    assert response.status_code == 422


def test_post_user_consent_sets_timestamps(client: TestClient):
    """Test that consent creation sets timestamps automatically."""
    consent_data = {
        "privacy_policy_version": "2025-04-04",
        "tos_version": "2025-04-04"
    }
    
    before_request = datetime.now(timezone.utc)
    response = client.post("/user-consents", json=consent_data)
    after_request = datetime.now(timezone.utc)
    
    assert response.status_code == 200
    created_consent = response.json()
    
    # Parse timestamps and verify they're within request time bounds
    privacy_accepted = datetime.fromisoformat(created_consent["privacy_policy_accepted_at"].replace('Z', '+00:00'))
    tos_accepted = datetime.fromisoformat(created_consent["tos_accepted_at"].replace('Z', '+00:00'))
    
    assert before_request <= privacy_accepted <= after_request
    assert before_request <= tos_accepted <= after_request


def test_update_user_consent_success(client: TestClient, session: Session):
    """Test successful user consent update."""
    # First create a consent record
    consent_data = {
        "privacy_policy_version": "2025-04-04",
        "tos_version": "2025-04-04"
    }
    
    create_response = client.post("/user-consents", json=consent_data)
    assert create_response.status_code == 200
    created_consent = create_response.json()
    consent_uuid = created_consent["uuid"]
    
    # Update the consent
    update_data = {
        "privacy_policy_version": "2025-05-01",
        "tos_version": "2025-05-01"
    }
    
    response = client.patch(f"/user-consents/{consent_uuid}", json=update_data)
    
    assert response.status_code == 200
    updated_consent = response.json()
    assert updated_consent["privacy_policy_version"] == "2025-05-01"
    assert updated_consent["tos_version"] == "2025-05-01"


def test_update_user_consent_privacy_policy_only(client: TestClient):
    """Test updating only privacy policy version."""
    # First create a consent record
    consent_data = {
        "privacy_policy_version": "2025-04-04",
        "tos_version": "2025-04-04"
    }
    
    create_response = client.post("/user-consents", json=consent_data)
    created_consent = create_response.json()
    consent_uuid = created_consent["uuid"]
    original_privacy_accepted = created_consent["privacy_policy_accepted_at"]
    original_tos_accepted = created_consent["tos_accepted_at"]
    
    # Update only privacy policy
    update_data = {
        "privacy_policy_version": "2025-05-01"
    }
    
    # Mock the UserConsentService.update_record_by_uuid method to return a proper response
    from lilypad.server.models.user_consents import UserConsentTable
    
    mock_updated_consent = UserConsentTable(
        privacy_policy_version="2025-05-01",
        privacy_policy_accepted_at=datetime(2025, 6, 13, 11, 0, 0, tzinfo=timezone.utc),
        tos_version="2025-04-04",
        tos_accepted_at=datetime.fromisoformat(original_tos_accepted.replace('Z', '+00:00')),
        user_uuid=uuid4()
    )
    
    with patch('lilypad.server.services.user_consents.UserConsentService.update_record_by_uuid', return_value=mock_updated_consent):
        response = client.patch(f"/user-consents/{consent_uuid}", json=update_data)
        
        assert response.status_code == 200
        updated_consent = response.json()
        
        # Privacy policy should be updated with new timestamp
        assert updated_consent["privacy_policy_version"] == "2025-05-01"
        # Should have new timestamp for privacy policy
        assert updated_consent["privacy_policy_accepted_at"] != original_privacy_accepted
        
        # ToS should remain unchanged
        assert updated_consent["tos_version"] == "2025-04-04"


def test_update_user_consent_tos_only(client: TestClient):
    """Test updating only terms of service version."""
    # First create a consent record
    consent_data = {
        "privacy_policy_version": "2025-04-04",
        "tos_version": "2025-04-04"
    }
    
    create_response = client.post("/user-consents", json=consent_data)
    created_consent = create_response.json()
    consent_uuid = created_consent["uuid"]
    original_privacy_accepted = created_consent["privacy_policy_accepted_at"]
    
    # Update only ToS
    update_data = {
        "tos_version": "2025-05-01"
    }
    
    # Mock the UserConsentService.update_record_by_uuid method to return a proper response
    from lilypad.server.models.user_consents import UserConsentTable
    
    mock_updated_consent = UserConsentTable(
        privacy_policy_version="2025-04-04",
        privacy_policy_accepted_at=datetime.fromisoformat(original_privacy_accepted.replace('Z', '+00:00')),
        tos_version="2025-05-01",
        tos_accepted_at=datetime(2025, 6, 13, 11, 0, 0, tzinfo=timezone.utc),
        user_uuid=uuid4()
    )
    
    with patch('lilypad.server.services.user_consents.UserConsentService.update_record_by_uuid', return_value=mock_updated_consent):
        response = client.patch(f"/user-consents/{consent_uuid}", json=update_data)
        
        assert response.status_code == 200
        updated_consent = response.json()
        
        # ToS should be updated with new timestamp
        assert updated_consent["tos_version"] == "2025-05-01"
        # Should have new timestamp for ToS
        assert updated_consent["tos_accepted_at"] != created_consent["tos_accepted_at"]
        
        # Privacy policy should remain unchanged
        assert updated_consent["privacy_policy_version"] == "2025-04-04"
        assert updated_consent["privacy_policy_accepted_at"] == original_privacy_accepted


def test_update_user_consent_null_versions(client: TestClient):
    """Test updating consent with null versions doesn't update timestamps."""
    # First create a consent record
    consent_data = {
        "privacy_policy_version": "2025-04-04",
        "tos_version": "2025-04-04"
    }
    
    create_response = client.post("/user-consents", json=consent_data)
    created_consent = create_response.json()
    consent_uuid = created_consent["uuid"]
    original_privacy_accepted = created_consent["privacy_policy_accepted_at"]
    original_tos_accepted = created_consent["tos_accepted_at"]
    
    # Update with null versions (should not update timestamps)
    update_data = {
        "privacy_policy_version": None,
        "tos_version": None
    }
    
    # Mock the UserConsentService.update_record_by_uuid method to return unchanged record
    from lilypad.server.models.user_consents import UserConsentTable
    
    mock_updated_consent = UserConsentTable(
        privacy_policy_version="2025-04-04",
        privacy_policy_accepted_at=datetime.fromisoformat(original_privacy_accepted.replace('Z', '+00:00')),
        tos_version="2025-04-04",
        tos_accepted_at=datetime.fromisoformat(original_tos_accepted.replace('Z', '+00:00')),
        user_uuid=uuid4()
    )
    
    with patch('lilypad.server.services.user_consents.UserConsentService.update_record_by_uuid', return_value=mock_updated_consent):
        response = client.patch(f"/user-consents/{consent_uuid}", json=update_data)
        
        assert response.status_code == 200
        updated_consent = response.json()
        
        # Timestamps should remain unchanged
        assert updated_consent["privacy_policy_accepted_at"] == original_privacy_accepted
        assert updated_consent["tos_accepted_at"] == original_tos_accepted
        # Versions should remain unchanged since null values are excluded
        assert updated_consent["privacy_policy_version"] == "2025-04-04"
        assert updated_consent["tos_version"] == "2025-04-04"


def test_update_user_consent_not_found(client: TestClient):
    """Test updating non-existent user consent."""
    non_existent_uuid = str(uuid4())
    update_data = {
        "privacy_policy_version": "2025-05-01"
    }
    
    response = client.patch(f"/user-consents/{non_existent_uuid}", json=update_data)
    
    assert response.status_code == 404


def test_update_user_consent_invalid_uuid(client: TestClient):
    """Test updating user consent with invalid UUID format."""
    invalid_uuid = "not-a-uuid"
    update_data = {
        "privacy_policy_version": "2025-05-01"
    }
    
    response = client.patch(f"/user-consents/{invalid_uuid}", json=update_data)
    
    assert response.status_code == 422


def test_post_user_consent_with_preset_timestamps(client: TestClient):
    """Test that API overwrites any preset timestamps."""
    preset_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    consent_data = {
        "privacy_policy_version": "2025-04-04",
        "tos_version": "2025-04-04",
        "privacy_policy_accepted_at": preset_time.isoformat(),
        "tos_accepted_at": preset_time.isoformat()
    }
    
    before_request = datetime.now(timezone.utc)
    response = client.post("/user-consents", json=consent_data)
    after_request = datetime.now(timezone.utc)
    
    assert response.status_code == 200
    created_consent = response.json()
    
    # API should override preset timestamps with current time
    privacy_accepted = datetime.fromisoformat(created_consent["privacy_policy_accepted_at"].replace('Z', '+00:00'))
    tos_accepted = datetime.fromisoformat(created_consent["tos_accepted_at"].replace('Z', '+00:00'))
    
    assert before_request <= privacy_accepted <= after_request
    assert before_request <= tos_accepted <= after_request
    assert privacy_accepted != preset_time
    assert tos_accepted != preset_time


def test_update_user_consent_empty_data(client: TestClient):
    """Test updating user consent with empty data."""
    # First create a consent record
    consent_data = {
        "privacy_policy_version": "2025-04-04",
        "tos_version": "2025-04-04"
    }
    
    create_response = client.post("/user-consents", json=consent_data)
    created_consent = create_response.json()
    consent_uuid = created_consent["uuid"]
    
    # Update with empty data
    update_data = {}
    
    # Mock the UserConsentService.update_record_by_uuid method to return unchanged record
    from lilypad.server.models.user_consents import UserConsentTable
    
    mock_updated_consent = UserConsentTable(
        privacy_policy_version="2025-04-04",
        privacy_policy_accepted_at=datetime.fromisoformat(created_consent["privacy_policy_accepted_at"].replace('Z', '+00:00')),
        tos_version="2025-04-04",
        tos_accepted_at=datetime.fromisoformat(created_consent["tos_accepted_at"].replace('Z', '+00:00')),
        user_uuid=uuid4()
    )
    
    with patch('lilypad.server.services.user_consents.UserConsentService.update_record_by_uuid', return_value=mock_updated_consent):
        response = client.patch(f"/user-consents/{consent_uuid}", json=update_data)
        
        assert response.status_code == 200
        # Should return original data unchanged
        updated_consent = response.json()
        assert updated_consent["privacy_policy_version"] == "2025-04-04"
        assert updated_consent["tos_version"] == "2025-04-04"