"""Test configuration and fixtures."""

from uuid import UUID, uuid4

import pytest
from sqlmodel import Session, SQLModel, create_engine

from lilypad.server.models import (
    UserRole,
)
from lilypad.server.models.organizations import Organization
from lilypad.server.models.user_organizations import UserOrganization
from lilypad.server.models.users import User

# In-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

ORGANIZATION_UUID = UUID("12345678-1234-1234-1234-123456789abc")


def get_session():
    """Get database session."""
    with Session(engine) as session:
        yield session


@pytest.fixture(autouse=True)
def setup_test_db():
    """Set up test database."""
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def db_session():
    """Get database session."""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user() -> User:
    """Create a test user and organization."""
    user_uuid = uuid4()
    organization = Organization(uuid=ORGANIZATION_UUID, name="Test Organization")
    user_org = UserOrganization(
        uuid=uuid4(),
        user_uuid=user_uuid,
        organization_uuid=ORGANIZATION_UUID,
        role=UserRole.ADMIN,
        organization=organization,
    )
    user = User(
        uuid=user_uuid,
        email="test@test.com",
        first_name="Test User",
        active_organization_uuid=ORGANIZATION_UUID,
        user_organizations=[user_org],
    )

    return user


@pytest.fixture
def get_test_current_user(test_user: User):
    """Override the get_current_user dependency for FastAPI.

    Returns:
        UserPublic: Test user
    """

    def override_get_current_user():
        return test_user

    return override_get_current_user
