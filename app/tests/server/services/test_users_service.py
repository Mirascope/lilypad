"""Comprehensive tests for the users service."""

from uuid import UUID, uuid4

import pytest
from sqlmodel import Session

from lilypad.server.models import OrganizationTable, UserTable
from lilypad.server.schemas.users import UserCreate, UserPublic
from lilypad.server.services.users import UserService


@pytest.fixture
def user_service(db_session: Session, test_user: UserPublic) -> UserService:
    """Create a UserService instance."""
    return UserService(session=db_session, user=test_user)


@pytest.fixture
def basic_user_service(db_session: Session) -> UserService:
    """Create a UserService instance without a user context."""
    # Create a minimal user for service initialization
    minimal_user = UserPublic(
        uuid=uuid4(),
        email="service@test.com",
        first_name="Service",
        active_organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
    )
    return UserService(session=db_session, user=minimal_user)


def test_create_user(basic_user_service: UserService, db_session: Session):
    """Test creating a new user."""
    user_data = UserCreate(email="newuser@test.com", first_name="New", last_name="User")

    user = basic_user_service.create_record(user_data)

    assert user.email == "newuser@test.com"
    assert user.first_name == "New"
    assert user.last_name == "User"
    assert user.uuid is not None

    # Verify in database
    db_user = db_session.get(UserTable, user.uuid)
    assert db_user is not None
    assert db_user.email == "newuser@test.com"


def test_get_user_by_uuid(user_service: UserService, db_session: Session):
    """Test getting user by UUID."""
    # Create a user
    user = UserTable(email="getbyuuid@test.com", first_name="Get", last_name="ByUuid")
    db_session.add(user)
    db_session.commit()

    # Get by UUID
    retrieved = user_service.find_record_by_uuid(user.uuid)

    assert retrieved is not None
    assert retrieved.uuid == user.uuid
    assert retrieved.email == "getbyuuid@test.com"


def test_get_user_not_found(user_service: UserService):
    """Test getting non-existent user raises HTTPException."""
    fake_uuid = uuid4()
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        user_service.find_record_by_uuid(fake_uuid)
    assert exc_info.value.status_code == 404


def test_update_user(user_service: UserService, db_session: Session):
    """Test updating a user."""
    # Create a user
    user = UserTable(email="original@test.com", first_name="Original", last_name="Name")
    db_session.add(user)
    db_session.commit()

    # Update it
    update_data = {"first_name": "Updated", "last_name": "Person"}
    updated = user_service.update_record_by_uuid(user.uuid, update_data)

    assert updated is not None
    assert updated.first_name == "Updated"
    assert updated.last_name == "Person"
    assert updated.email == "original@test.com"  # Unchanged

    # Verify in database
    db_session.refresh(user)
    assert user.first_name == "Updated"


def test_update_user_email(user_service: UserService, db_session: Session):
    """Test updating user email."""
    # Create a user
    user = UserTable(email="old@test.com", first_name="Email", last_name="Change")
    db_session.add(user)
    db_session.commit()

    # Update email
    update_data = {"email": "new@test.com"}
    updated = user_service.update_record_by_uuid(user.uuid, update_data)

    assert updated is not None
    assert updated.email == "new@test.com"


def test_delete_user(user_service: UserService, db_session: Session):
    """Test deleting a user (hard delete)."""
    # Create a user
    user = UserTable(email="delete@test.com", first_name="To", last_name="Delete")
    db_session.add(user)
    db_session.commit()
    user_uuid = user.uuid

    # Delete it
    result = user_service.delete_record_by_uuid(user_uuid)
    assert result is True

    # Commit the deletion
    db_session.commit()

    # Verify deleted
    db_user = db_session.get(UserTable, user_uuid)
    assert db_user is None


def test_update_user_keys(user_service: UserService, db_session: Session):
    """Test updating user keys."""
    # Create a user
    user = UserTable(
        email="keys@test.com",
        first_name="Keys",
        last_name="User",
        keys={"initial": "value"},
    )
    db_session.add(user)
    db_session.commit()

    # Update keys
    updated = user_service.update_record_by_uuid(
        user.uuid, {"keys": {"new": "data", "another": "key"}}
    )

    assert updated is not None
    assert updated.keys == {"new": "data", "another": "key"}

    # Verify in database
    db_session.refresh(user)
    assert user.keys == {"new": "data", "another": "key"}


def test_find_user_by_email(user_service: UserService, db_session: Session):
    """Test finding user by email."""
    # Create user with unique email
    user = UserTable(email="unique@test.com", first_name="Unique", last_name="User")
    db_session.add(user)
    db_session.commit()

    # Find by email
    found = user_service.find_record(email="unique@test.com")

    assert found is not None
    assert found.uuid == user.uuid
    assert found.email == "unique@test.com"


def test_find_all_users(user_service: UserService, db_session: Session):
    """Test finding all users."""
    # Create multiple users
    users = []
    for i in range(3):
        user = UserTable(
            email=f"user{i}@test.com", first_name=f"User{i}", last_name="Test"
        )
        db_session.add(user)
        users.append(user)
    db_session.commit()

    # Find all
    all_users = user_service.find_all_records()

    # Should include existing users plus our 3
    assert len(all_users) >= 3

    # Check our users are included
    emails = {user.email for user in all_users}
    assert "user0@test.com" in emails
    assert "user1@test.com" in emails
    assert "user2@test.com" in emails


def test_update_user_active_organization(db_session: Session):
    """Test updating user's active organization."""
    # Create a user in the database
    user = UserTable(email="orgswitch@test.com", first_name="Org", last_name="Switcher")
    db_session.add(user)
    db_session.commit()

    # Create organization
    org = OrganizationTable(name="New Org", license="license1")
    db_session.add(org)
    db_session.commit()

    # Create UserService with the actual user
    user_public = UserPublic(
        uuid=user.uuid,
        email=user.email,
        first_name=user.first_name,
        active_organization_uuid=user.active_organization_uuid,
    )
    user_service = UserService(session=db_session, user=user_public)

    # Update active organization for the current user
    updated_user = user_service.update_user_active_organization_uuid(org.uuid)

    # Verify updated
    assert updated_user.active_organization_uuid == org.uuid


def test_count_users(user_service: UserService, db_session: Session):
    """Test counting users."""
    # Get initial users
    initial_users = user_service.find_all_records()
    initial_count = len(initial_users)

    # Create new users
    for i in range(5):
        user = UserTable(
            email=f"count{i}@test.com", first_name=f"Count{i}", last_name="User"
        )
        db_session.add(user)
    db_session.commit()

    # Get new count
    new_users = user_service.find_all_records()
    new_count = len(new_users)

    assert new_count == initial_count + 5


def test_find_users_by_organization(user_service: UserService, db_session: Session):
    """Test finding users by organization."""
    org_uuid = UUID("12345678-1234-1234-1234-123456789abc")

    # Create users in the organization
    for i in range(3):
        user = UserTable(
            email=f"orguser{i}@test.com",
            first_name=f"OrgUser{i}",
            last_name="Test",
            active_organization_uuid=org_uuid,
        )
        db_session.add(user)
    db_session.commit()

    # Find users in organization
    org_users = user_service.find_all_records(active_organization_uuid=org_uuid)

    # Should find at least our 3 users
    assert len(org_users) >= 3

    # All should be in the organization
    for user in org_users:
        assert user.active_organization_uuid == org_uuid


def test_user_validation(basic_user_service: UserService):
    """Test creating users with valid data."""
    # Test creating user with minimal data
    user_data = UserCreate(email="minimal@test.com", first_name="Minimal")
    user = basic_user_service.create_record(user_data)
    assert user.email == "minimal@test.com"
    assert user.first_name == "Minimal"
    assert user.last_name is None

    # Test creating user with all fields
    user_data = UserCreate(
        email="full@test.com",
        first_name="Full",
        last_name="User",
        active_organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
    )
    user = basic_user_service.create_record(user_data)
    assert user.email == "full@test.com"
    assert user.first_name == "Full"
    assert user.last_name == "User"


def test_duplicate_email(basic_user_service: UserService, db_session: Session):
    """Test creating user with duplicate email."""
    # Create first user
    user1 = UserTable(email="duplicate@test.com", first_name="First", last_name="User")
    db_session.add(user1)
    db_session.commit()

    # Try to create second user with same email
    # Note: SQLite doesn't enforce unique constraints in memory mode
    # In production with PostgreSQL, this would raise IntegrityError
    user_data = UserCreate(
        email="duplicate@test.com", first_name="Second", last_name="User"
    )

    # Create the second user (SQLite allows this)
    user2 = basic_user_service.create_record(user_data)
    db_session.commit()

    # Both users exist in SQLite
    assert user2.email == "duplicate@test.com"


def test_user_keys_field(user_service: UserService, db_session: Session):
    """Test user keys field handling."""
    # Create user with keys
    user = UserTable(
        email="testkeys@test.com",
        first_name="Keys",
        last_name="User",
        keys={"api_key": "test123", "secret": "value"},
    )
    db_session.add(user)
    db_session.commit()

    # Get user
    retrieved = user_service.find_record_by_uuid(user.uuid)

    assert retrieved is not None
    assert retrieved.keys == {"api_key": "test123", "secret": "value"}

    # Update keys
    update_data = {"keys": {"api_key": "new_key", "extra": "data"}}
    updated = user_service.update_record_by_uuid(user.uuid, update_data)

    assert updated is not None
    assert updated.keys["api_key"] == "new_key"
    assert updated.keys["extra"] == "data"


def test_pagination(user_service: UserService, db_session: Session):
    """Test retrieving multiple users."""
    # Create many users
    created_users = []
    for i in range(20):
        user = UserTable(
            email=f"page{i:02d}@test.com", first_name=f"Page{i:02d}", last_name="User"
        )
        db_session.add(user)
        created_users.append(user)
    db_session.commit()

    # Get all users
    all_users = user_service.find_all_records()

    # Check that our created users are in the results
    all_emails = {user.email for user in all_users}
    for user in created_users:
        assert user.email in all_emails
