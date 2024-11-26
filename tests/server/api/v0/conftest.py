"""Pytest configuration for FastAPI tests."""

from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from lilypad.server.api.v0.main import api
from lilypad.server.db.session import get_session

# Create a single test engine for all tests
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)


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
def client(
    session: Session, get_test_session: AsyncGenerator[Session, None]
) -> TestClient:  # pyright: ignore [reportInvalidTypeForm]
    """Create a test client with database session dependency override.

    Args:
        session: The database session
        get_test_session: Session dependency override

    Returns:
        TestClient: FastAPI test client
    """
    api.dependency_overrides[get_session] = get_test_session  # pyright: ignore [reportArgumentType]

    client = TestClient(api)
    try:
        yield client  # pyright: ignore [reportReturnType]
    finally:
        api.dependency_overrides.clear()
