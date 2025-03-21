"""Test configuration and fixtures."""

from collections.abc import Callable, Generator
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlmodel import Session, SQLModel, create_engine

from ee import LicenseInfo, Tier
from lilypad.ee.server.models import (
    UserRole,
)
from lilypad.ee.server.schemas.user_organizations import UserOrganizationPublic
from lilypad.server.schemas import (
    OrganizationPublic,
    UserPublic,
)

# In-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

ORGANIZATION_UUID = UUID("12345678-1234-1234-1234-123456789abc")


def get_session() -> Generator[Session, None, None]:
    """Get database session."""
    with Session(engine) as session:
        yield session


@pytest.fixture(autouse=True)
def setup_test_db() -> Generator[None, None, None]:
    """Set up test database."""
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Get database session."""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user() -> UserPublic:
    """Create a test user and organization."""
    user_uuid = uuid4()
    organization = OrganizationPublic(uuid=ORGANIZATION_UUID, name="Test Organization")
    user_org = UserOrganizationPublic(
        uuid=uuid4(),
        user_uuid=user_uuid,
        organization_uuid=ORGANIZATION_UUID,
        role=UserRole.ADMIN,
        organization=organization,
    )
    user_public = UserPublic(
        uuid=user_uuid,
        email="test@test.com",
        first_name="Test User",
        active_organization_uuid=ORGANIZATION_UUID,
        user_organizations=[user_org],
    )

    return user_public


@pytest.fixture
def get_test_current_user(test_user: UserPublic) -> Callable[[], UserPublic]:
    """Override the get_current_user dependency for FastAPI.

    Returns:
        UserPublic: Test user
    """

    def override_get_current_user() -> UserPublic:
        return test_user

    return override_get_current_user


@pytest.fixture(autouse=True)
def mock_license_info() -> Generator[LicenseInfo, None, None]:
    """Override the get_license_info dependency for FastAPI.

    Returns:
        LicenseInfo: Test license info
    """
    # patch LicenseValidator._verify_license method
    with patch("ee.validate.LicenseValidator.validate_license") as mock_verify_license:
        license_info = mock_verify_license.return_value = LicenseInfo(
            organization_uuid=ORGANIZATION_UUID,
            tier=Tier.ENTERPRISE,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            customer="test",
            license_id="test_id",
        )
        yield license_info
