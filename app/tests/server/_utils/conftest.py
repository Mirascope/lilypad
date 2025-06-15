"""Conftest for server utils tests."""

import pytest
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from lilypad.server.models.base_sql_model import BaseSQLModel


@pytest.fixture
def db_session():
    """Create an in-memory database session for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    BaseSQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session
