"""Tests for the API keys service."""

from uuid import uuid4
import pytest
from sqlmodel import Session

from lilypad.server.models.api_keys import APIKeyTable
from lilypad.server.schemas.api_keys import APIKeyCreate
from lilypad.server.schemas.users import UserPublic
from lilypad.server.services.api_keys import APIKeyService


@pytest.fixture
def api_key_service(db_session: Session, test_user: UserPublic) -> APIKeyService:
    """Create an APIKeyService instance."""
    return APIKeyService(session=db_session, user=test_user)


def test_find_keys_by_user_and_project(api_key_service: APIKeyService, db_session: Session):
    """Test finding API keys by user and project."""
    project_uuid = uuid4()
    
    # Create an API key for the project
    api_key_data = APIKeyCreate(name="Test Key", project_uuid=project_uuid, key_hash="abcdef123456")
    created_key = api_key_service.create_record(api_key_data)
    
    # Find keys by project
    found_keys = api_key_service.find_keys_by_user_and_project(project_uuid)
    
    # Should find the created key
    assert len(found_keys) >= 1
    assert any(key.uuid == created_key.uuid for key in found_keys)


def test_find_keys_by_user_and_project_no_keys(api_key_service: APIKeyService):
    """Test finding API keys for project with no keys."""
    project_uuid = uuid4()
    
    # Find keys for project with no keys
    found_keys = api_key_service.find_keys_by_user_and_project(project_uuid)
    
    # Should return empty list
    assert len(found_keys) == 0


def test_create_record_adds_user_uuid(api_key_service: APIKeyService, db_session: Session):
    """Test that create_record automatically adds user_uuid."""
    project_uuid = uuid4()
    
    # Create an API key
    api_key_data = APIKeyCreate(name="Test Key", project_uuid=project_uuid, key_hash="abcdef789012")
    created_key = api_key_service.create_record(api_key_data)
    
    # Should have user_uuid set
    assert created_key.user_uuid == api_key_service.user.uuid
    assert created_key.name == "Test Key"
    assert created_key.project_uuid == project_uuid