"""Pytest configuration for FastAPI tests."""

from collections.abc import AsyncGenerator, Generator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from lilypad.ee.server.api.v0.main import api
from lilypad.server._utils import get_current_user, match_api_key_with_project
from lilypad.server.db.session import get_session
from lilypad.server.models import (
    APIKeyTable,
    GenerationTable,
    OrganizationTable,
    ProjectTable,
    UserOrganizationTable,
    UserPublic,
    UserRole,
    UserTable,
)

# Create a single test engine for all tests
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
ORGANIZATION_UUID = UUID("12345678-1234-1234-1234-123456789abc")


@pytest.fixture(scope="session", autouse=True)
def create_test_database() -> None:
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
def client(
    session: Session,
    get_test_session: AsyncGenerator[Session, None],
    get_test_current_user: UserPublic,
) -> TestClient:  # pyright: ignore [reportInvalidTypeForm]
    """Create a test client with database session dependency override.

    Args:
        session: The database session
        get_test_session: Session dependency override
        get_test_current_user: Current user dependency override

    Returns:
        TestClient: FastAPI test client
    """

    def _override() -> bool:
        return True

    api.dependency_overrides[match_api_key_with_project] = _override
    api.dependency_overrides[get_session] = get_test_session  # pyright: ignore [reportArgumentType]
    api.dependency_overrides[get_current_user] = get_test_current_user  # pyright: ignore [reportArgumentType]

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
    organization = OrganizationTable(uuid=ORGANIZATION_UUID, name="Test Organization")
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
def test_api_key(
    session: Session, test_project: ProjectTable
) -> Generator[APIKeyTable, None, None]:
    """Create a test api key.

    Args:
        session: Database session
        test_project: Parent project

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
        organization_uuid=test_project.organization_uuid,
    )
    session.add(function)
    session.commit()
    session.refresh(function)
    yield function
