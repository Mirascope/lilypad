import pytest
from sqlmodel import Session, SQLModel, select

from lilypad.server.db.session import engine, get_session
from lilypad.server.models import ProjectTable


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test"""
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)

def test_get_session():
    """Test getting a database session"""
    session = next(get_session())
    assert isinstance(session, Session)

    # Test session can execute queries
    project = ProjectTable(name="Test Project")
    session.add(project)
    session.commit()

    # Verify project was committed
    stmt = select(ProjectTable)
    result = session.exec(stmt).first()
    assert result.name == "Test Project"

def test_session_rollback():
    """Test session rollback on error"""
    session = next(get_session())
    project = ProjectTable(name="Test Project")
    session.add(project)

    try:
        # Force an error by adding duplicate project
        duplicate = ProjectTable(name="Test Project")
        session.add(duplicate)
        session.commit()
    except Exception:
        session.rollback()

    # Verify original project was not committed
    stmt = select(ProjectTable)
    result = session.exec(stmt).all()
    assert len(result) == 0