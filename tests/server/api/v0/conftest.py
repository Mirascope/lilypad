"""Pytest configuration for FastAPI tests."""

from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from ee.validate import LicenseInfo, Tier
from lilypad.ee.server.models import EnvironmentTable
from lilypad.ee.server.require_license import get_organization_license
from lilypad.server._utils import get_current_user
from lilypad.server.api.v0.main import api
from lilypad.server.db.session import get_session
from lilypad.server.models import (
    APIKeyTable,
    GenerationTable,
    OrganizationTable,
    ProjectTable,
    UserOrganizationTable,
    UserRole,
    UserTable,
)
from lilypad.server.schemas import UserPublic

# Create a single test engine for all tests
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
ORGANIZATION_UUID = UUID("12345678-1234-1234-1234-123456789abc")


@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """Create test database once for test session."""
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture
def session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test.

    Yields:
        Session: The database session
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def get_test_session(
    session: Session,
) -> Generator[AsyncGenerator[Session, None], None, None]:
    """Override the get_session dependency for FastAPI.

    Args:
        session: The test database session

    Yields:
        AsyncGenerator[Session, None]: Async session generator
    """

    async def override_get_session() -> AsyncGenerator[Session, None]:
        try:
            yield session
        finally:
            pass  # Session is handled by the session fixture

    return override_get_session  # pyright: ignore [reportReturnType]


@pytest.fixture
def get_test_organization_license():
    """Override the get_organization_license dependency for FastAPI.

    Returns:
        UserPublic: Test user
    """

    def override_get_organization_license():
        return LicenseInfo(
            customer="mock_customer",
            license_id="mock_license",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            tier=Tier.FREE,
            organization_uuid=UUID("123e4567-e89b-12d3-a456-426614174000"),
        )

    return override_get_organization_license


@pytest.fixture
def client(
    session: Session,
    get_test_session: AsyncGenerator[Session, None],
    get_test_current_user: UserPublic,
    get_test_organization_license: LicenseInfo,
) -> TestClient:  # pyright: ignore [reportInvalidTypeForm]
    """Create a test client with database session dependency override.

    Args:
        session: The database session
        get_test_session: Session dependency override
        get_test_current_user: Current user dependency override
        get_test_organization_license: Organization license dependency override

    Returns:
        TestClient: FastAPI test client
    """
    api.dependency_overrides[get_session] = get_test_session  # pyright: ignore [reportArgumentType]
    api.dependency_overrides[get_current_user] = get_test_current_user  # pyright: ignore [reportArgumentType]
    api.dependency_overrides[get_organization_license] = get_test_organization_license  # pyright: ignore [reportArgumentType]

    client = TestClient(api)
    try:
        yield client  # pyright: ignore [reportReturnType]
    finally:
        api.dependency_overrides.clear()


@pytest.fixture
def test_user(session: Session) -> Generator[UserTable, None, None]:
    """Create a test user.

    Args:
        session: Database session

    Yields:
        UserTable: Test user
    """
    user_uuid = uuid4()
    organization = OrganizationTable(
        uuid=ORGANIZATION_UUID, name="Test Organization", license="123456"
    )
    session.add(organization)
    user = UserTable(
        uuid=user_uuid,
        email="test@test.com",
        first_name="Test User",
        active_organization_uuid=ORGANIZATION_UUID,
    )
    session.add(user)
    user_org = UserOrganizationTable(
        user_uuid=user_uuid,
        organization_uuid=ORGANIZATION_UUID,
        role=UserRole.ADMIN,
        organization=organization,
    )
    session.add(user_org)
    session.commit()
    session.refresh(user)
    yield user


@pytest.fixture
def test_project(session: Session) -> Generator[ProjectTable, None, None]:
    """Create a test project.

    Args:
        session: Database session

    Yields:
        ProjectTable: Test project
    """
    project = ProjectTable(name="test_project", organization_uuid=ORGANIZATION_UUID)
    session.add(project)
    session.commit()
    session.refresh(project)
    yield project


@pytest.fixture
def test_environment(
    session: Session, test_project: ProjectTable
) -> Generator[EnvironmentTable, None, None]:
    """Create a test environment.

    Args:
        session: Database session
        test_project: Parent project

    Yields:
        EnvironmentTable: Test environment
    """
    environment = EnvironmentTable(
        name="test_environment",
        project_uuid=test_project.uuid,  # pyright: ignore [reportArgumentType]
        organization_uuid=ORGANIZATION_UUID,
    )
    session.add(environment)
    session.commit()
    session.refresh(environment)
    yield environment


@pytest.fixture
def test_api_key(
    session: Session, test_project: ProjectTable, test_environment: EnvironmentTable
) -> Generator[APIKeyTable, None, None]:
    """Create a test api key.

    Args:
        session: Database session
        test_project: Parent project
        test_environment: Parent environment

    Yields:
        APIKeyTable
    """
    if not test_project.uuid:
        raise ValueError("Project UUID is required for API key creation")

    api_key = APIKeyTable(
        key_hash="test_key",
        user_uuid=uuid4(),
        organization_uuid=ORGANIZATION_UUID,
        name="test_key",
        project_uuid=test_project.uuid,
        environment_uuid=test_environment.uuid,  # pyright: ignore [reportArgumentType]
    )
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    yield api_key


@pytest.fixture
def test_generation(
    session: Session, test_project: ProjectTable
) -> Generator[GenerationTable, None, None]:
    """Create a test generation.

    Args:
        session: Database session
        test_project: Parent project

    Yields:
        GenerationTable: Test generation
    """
    function = GenerationTable(
        project_uuid=test_project.uuid,
        name="test_function",
        signature="def test(): pass",
        code="def test(): pass",
        hash="test_hash",
        arg_types={},
        organization_uuid=test_project.organization_uuid,
    )
    session.add(function)
    session.commit()
    session.refresh(function)
    yield function
