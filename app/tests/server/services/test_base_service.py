"""Tests for base service."""

import pytest
from fastapi import HTTPException
from pydantic import BaseModel
from sqlmodel import Session
from uuid import uuid4

from lilypad.server.models.users import UserTable
from lilypad.server.services.base import BaseService


class MockCreateModel(BaseModel):
    """Mock create model for testing."""
    email: str
    first_name: str


class TestableBaseService(BaseService[UserTable, MockCreateModel]):
    """Testable implementation of BaseService."""
    table = UserTable
    create_model = MockCreateModel


@pytest.fixture
def test_user_table(db_session: Session, test_user) -> UserTable:
    """Create a test user table record."""
    user_table = UserTable(
        uuid=test_user.uuid,
        email=test_user.email,
        first_name=test_user.first_name,
        active_organization_uuid=test_user.active_organization_uuid,
    )
    db_session.add(user_table)
    db_session.commit()
    db_session.refresh(user_table)
    return user_table


def test_find_record(db_session: Session, test_user, test_user_table):
    """Test find_record method."""
    service = TestableBaseService(session=db_session, user=test_user)
    
    # Find existing record
    found_user = service.find_record(email=test_user_table.email)
    assert found_user is not None
    assert found_user.email == test_user_table.email
    
    # Find non-existent record
    not_found = service.find_record(email="nonexistent@example.com")
    assert not_found is None


def test_find_record_by_uuid(db_session: Session, test_user, test_user_table):
    """Test find_record_by_uuid method."""
    service = TestableBaseService(session=db_session, user=test_user)
    
    # Find existing record
    found_user = service.find_record_by_uuid(test_user_table.uuid)
    assert found_user.uuid == test_user_table.uuid
    assert found_user.email == test_user_table.email
    
    # Find non-existent record
    with pytest.raises(HTTPException) as exc_info:
        service.find_record_by_uuid(uuid4())
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail


def test_find_records_by_uuids(db_session: Session, test_user, test_user_table):
    """Test find_records_by_uuids method."""
    service = TestableBaseService(session=db_session, user=test_user)
    
    # Create another user
    user2 = UserTable(
        email="user2@example.com",
        first_name="User2",
        active_organization_uuid=test_user.active_organization_uuid,
    )
    db_session.add(user2)
    db_session.commit()
    db_session.refresh(user2)
    
    # Find multiple records
    uuids = {test_user_table.uuid, user2.uuid}
    found_users = service.find_records_by_uuids(uuids)
    assert len(found_users) == 2
    found_uuids = {user.uuid for user in found_users}
    assert found_uuids == uuids
    
    # Test with empty set
    empty_result = service.find_records_by_uuids(set())
    assert len(empty_result) == 0
    
    # Test with additional filters
    filtered_users = service.find_records_by_uuids(
        uuids, email=test_user_table.email
    )
    assert len(filtered_users) == 1
    assert filtered_users[0].uuid == test_user_table.uuid


def test_find_all_records(db_session: Session, test_user, test_user_table):
    """Test find_all_records method."""
    service = TestableBaseService(session=db_session, user=test_user)
    
    # Find all records
    all_users = service.find_all_records()
    assert len(all_users) >= 1
    assert test_user_table.uuid in {user.uuid for user in all_users}
    
    # Find with filters
    filtered_users = service.find_all_records(email=test_user_table.email)
    assert len(filtered_users) == 1
    assert filtered_users[0].uuid == test_user_table.uuid


def test_delete_record_by_uuid(db_session: Session, test_user):
    """Test delete_record_by_uuid method."""
    service = TestableBaseService(session=db_session, user=test_user)
    
    # Create a test user to delete
    user_to_delete = UserTable(
        email="delete_me@example.com",
        first_name="DeleteMe",
        active_organization_uuid=test_user.active_organization_uuid,
    )
    db_session.add(user_to_delete)
    db_session.commit()
    db_session.refresh(user_to_delete)
    
    # Delete the user
    result = service.delete_record_by_uuid(user_to_delete.uuid)
    assert result is True
    
    # Verify deletion
    with pytest.raises(HTTPException):
        service.find_record_by_uuid(user_to_delete.uuid)
    
    # Try to delete non-existent record
    with pytest.raises(HTTPException):
        service.delete_record_by_uuid(uuid4())


def test_delete_record_exception_handling(db_session: Session, test_user, monkeypatch):
    """Test delete_record_by_uuid exception handling."""
    service = TestableBaseService(session=db_session, user=test_user)
    
    # Create a test user
    user_to_delete = UserTable(
        email="delete_exception@example.com",
        first_name="DeleteException",
        active_organization_uuid=test_user.active_organization_uuid,
    )
    db_session.add(user_to_delete)
    db_session.commit()
    db_session.refresh(user_to_delete)
    
    # Mock session.delete to raise an exception
    def mock_delete(record):
        raise Exception("Delete failed")
    
    monkeypatch.setattr(db_session, "delete", mock_delete)
    
    # Delete should return False when exception occurs
    result = service.delete_record_by_uuid(user_to_delete.uuid)
    assert result is False


def test_create_record(db_session: Session, test_user):
    """Test create_record method."""
    service = TestableBaseService(session=db_session, user=test_user)
    
    # Create new record
    create_data = MockCreateModel(
        email="new_user@example.com",
        first_name="NewUser"
    )
    
    new_user = service.create_record(
        create_data,
        active_organization_uuid=test_user.active_organization_uuid
    )
    
    assert new_user.email == "new_user@example.com"
    assert new_user.first_name == "NewUser"
    assert new_user.uuid is not None
    assert new_user.active_organization_uuid == test_user.active_organization_uuid


def test_update_record_by_uuid(db_session: Session, test_user, test_user_table):
    """Test update_record_by_uuid method."""
    service = TestableBaseService(session=db_session, user=test_user)
    
    # Update existing record
    update_data = {"first_name": "UpdatedName"}
    updated_user = service.update_record_by_uuid(test_user_table.uuid, update_data)
    
    assert updated_user.uuid == test_user_table.uuid
    assert updated_user.first_name == "UpdatedName"
    assert updated_user.email == test_user_table.email  # Should remain unchanged
    
    # Try to update non-existent record
    with pytest.raises(HTTPException):
        service.update_record_by_uuid(uuid4(), {"first_name": "Whatever"})


def test_base_service_init(db_session: Session, test_user):
    """Test BaseService initialization."""
    service = TestableBaseService(session=db_session, user=test_user)
    
    assert service.session == db_session
    assert service.user == test_user
    assert service.table == UserTable
    assert service.create_model == MockCreateModel