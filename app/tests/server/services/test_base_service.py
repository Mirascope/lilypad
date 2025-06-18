"""Tests for base service."""

from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import BaseModel
from sqlmodel import Session

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


@pytest.fixture
def base_service(db_session: Session, test_user) -> TestableBaseService:
    """Create a testable base service instance."""
    return TestableBaseService(session=db_session, user=test_user)


# ===== Parameterized Tests for find_record =====


@pytest.mark.parametrize(
    "email,should_exist",
    [
        ("existing@example.com", True),
        ("nonexistent@example.com", False),
    ],
)
def test_find_record(base_service, test_user_table, email, should_exist):
    """Test find_record method with various inputs."""
    # Update test_user_table email for the test
    if should_exist:
        test_user_table.email = email
        base_service.session.add(test_user_table)
        base_service.session.commit()

    found_user = base_service.find_record(email=email)

    if should_exist:
        assert found_user is not None
        assert found_user.email == email
    else:
        assert found_user is None


# ===== Parameterized Tests for find_record_by_uuid =====


@pytest.mark.parametrize(
    "use_existing,expected_status",
    [
        (True, 200),  # Existing record
        (False, 404),  # Non-existent record
    ],
)
def test_find_record_by_uuid(
    base_service, test_user_table, use_existing, expected_status
):
    """Test find_record_by_uuid method."""
    uuid_to_find = test_user_table.uuid if use_existing else uuid4()

    if expected_status == 200:
        found_user = base_service.find_record_by_uuid(uuid_to_find)
        assert found_user.uuid == test_user_table.uuid
        assert found_user.email == test_user_table.email
    else:
        with pytest.raises(HTTPException) as exc_info:
            base_service.find_record_by_uuid(uuid_to_find)
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail


# ===== Parameterized Tests for find_records_by_uuids =====


@pytest.mark.parametrize(
    "num_users,filter_email,expected_count",
    [
        (2, None, 2),  # Find all created users
        (2, "user1@example.com", 1),  # Filter by email
        (0, None, 0),  # Empty set
    ],
)
def test_find_records_by_uuids(
    base_service, test_user_table, num_users, filter_email, expected_count
):
    """Test find_records_by_uuids method with various scenarios."""
    uuids = set()

    if num_users > 0:
        # Use existing test_user_table
        test_user_table.email = "user1@example.com"
        base_service.session.add(test_user_table)
        base_service.session.commit()
        uuids.add(test_user_table.uuid)

        # Create additional users if needed
        for i in range(1, num_users):
            user = UserTable(
                email=f"user{i + 1}@example.com",
                first_name=f"User{i + 1}",
                active_organization_uuid=test_user_table.active_organization_uuid,
            )
            base_service.session.add(user)
            base_service.session.commit()
            base_service.session.refresh(user)
            uuids.add(user.uuid)

    # Find records
    kwargs = {"email": filter_email} if filter_email else {}
    found_users = base_service.find_records_by_uuids(uuids, **kwargs)

    assert len(found_users) == expected_count
    if expected_count > 0:
        found_emails = {user.email for user in found_users}
        if filter_email:
            assert found_emails == {filter_email}


# ===== CRUD Operations Tests =====


def test_create_record(base_service, test_user):
    """Test create_record method."""
    create_data = MockCreateModel(email="new_user@example.com", first_name="NewUser")

    new_user = base_service.create_record(
        create_data, active_organization_uuid=test_user.active_organization_uuid
    )

    assert new_user.email == "new_user@example.com"
    assert new_user.first_name == "NewUser"
    assert new_user.uuid is not None
    assert new_user.active_organization_uuid == test_user.active_organization_uuid


@pytest.mark.parametrize(
    "update_data,field_to_check,expected_value",
    [
        ({"first_name": "UpdatedName"}, "first_name", "UpdatedName"),
        ({"email": "updated@example.com"}, "email", "updated@example.com"),
    ],
)
def test_update_record_by_uuid(
    base_service, test_user_table, update_data, field_to_check, expected_value
):
    """Test update_record_by_uuid method with various updates."""
    updated_user = base_service.update_record_by_uuid(test_user_table.uuid, update_data)

    assert updated_user.uuid == test_user_table.uuid
    assert getattr(updated_user, field_to_check) == expected_value

    # Check that other fields remain unchanged
    if field_to_check != "email":
        assert updated_user.email == test_user_table.email
    if field_to_check != "first_name":
        assert updated_user.first_name == test_user_table.first_name


def test_update_record_by_uuid_not_found(base_service):
    """Test update_record_by_uuid with non-existent record."""
    with pytest.raises(HTTPException):
        base_service.update_record_by_uuid(uuid4(), {"first_name": "Whatever"})


# ===== Delete Operations Tests =====


@pytest.mark.parametrize("should_succeed", [True, False])
def test_delete_record_by_uuid(base_service, should_succeed, monkeypatch):
    """Test delete_record_by_uuid with success and failure scenarios."""
    # Create a test user to delete
    user_to_delete = UserTable(
        email="delete_me@example.com",
        first_name="DeleteMe",
        active_organization_uuid=uuid4(),
    )
    base_service.session.add(user_to_delete)
    base_service.session.commit()
    base_service.session.refresh(user_to_delete)

    if not should_succeed:
        # Mock session.delete to raise an exception
        def mock_delete(record):
            raise Exception("Delete failed")

        monkeypatch.setattr(base_service.session, "delete", mock_delete)

    result = base_service.delete_record_by_uuid(user_to_delete.uuid)
    assert result == should_succeed

    if should_succeed:
        # Verify deletion
        with pytest.raises(HTTPException):
            base_service.find_record_by_uuid(user_to_delete.uuid)


def test_delete_record_by_uuid_not_found(base_service):
    """Test delete_record_by_uuid with non-existent record."""
    with pytest.raises(HTTPException):
        base_service.delete_record_by_uuid(uuid4())


# ===== Service Initialization Tests =====


def test_base_service_init(db_session: Session, test_user):
    """Test BaseService initialization."""
    service = TestableBaseService(session=db_session, user=test_user)

    assert service.session == db_session
    assert service.user == test_user
    assert service.table == UserTable
    assert service.create_model == MockCreateModel


# ===== Filtering Tests =====


@pytest.mark.parametrize(
    "filter_field,filter_value,expected_count",
    [
        ("email", "test@example.com", 1),
        ("first_name", "TestUser", 1),
        ("email", "nonexistent@example.com", 0),
    ],
)
def test_find_all_records_with_filters(
    base_service, test_user_table, filter_field, filter_value, expected_count
):
    """Test find_all_records with various filters."""
    # Set up test data
    test_user_table.email = "test@example.com"
    test_user_table.first_name = "TestUser"
    base_service.session.add(test_user_table)
    base_service.session.commit()

    # Find with filters
    kwargs = {filter_field: filter_value}
    filtered_users = base_service.find_all_records(**kwargs)

    assert len(filtered_users) == expected_count
    if expected_count > 0:
        assert getattr(filtered_users[0], filter_field) == filter_value
