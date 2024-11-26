"""Test configuration and fixtures."""

from collections.abc import Coroutine
from typing import Any
from uuid import UUID

import pytest
from sqlmodel import Session, SQLModel, create_engine

from lilypad.server.models import (
    OrganizationPublic,
    UserOrganizationPublic,
    UserPublic,
    UserRole,
)

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
def test_user() -> UserPublic:
    user_id = 1
    organization = OrganizationPublic(uuid=ORGANIZATION_UUID, name="Test Organization")
    user_org = UserOrganizationPublic(
        id=1,
        user_id=user_id,
        organization_uuid=ORGANIZATION_UUID,
        role=UserRole.ADMIN,
        organization=organization,
    )
    user_public = UserPublic(
        id=user_id,
        email="test@test.com",
        first_name="Test User",
        active_organization_uuid=ORGANIZATION_UUID,
        user_organizations=[user_org],
    )

    return user_public


@pytest.fixture
def get_test_current_user(test_user: UserPublic):
    """Override the get_current_user dependency for FastAPI.

    Returns:
        UserPublic: Test user
    """

    def override_get_current_user():
        return test_user

    return override_get_current_user
