"""Tests for database session management"""

from uuid import UUID

import pytest
from sqlmodel import Session, SQLModel, select

from lilypad.server.db.session import db, get_session, standalone_session
from lilypad.server.models import ProjectTable

ORGANIZATION_UUID = UUID("12345678-1234-1234-1234-123456789abc")


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test"""
    engine = db.get_engine()
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


def test_get_session():
    """Test getting a database session"""
    session = next(get_session())
    assert isinstance(session, Session)

    # Test session can execute queries
    project = ProjectTable(name="Test Project", organization_uuid=ORGANIZATION_UUID)
    session.add(project)
    session.commit()

    # Verify project was committed
    stmt = select(ProjectTable)
    result = session.exec(stmt).first()
    assert result.name == "Test Project"  # pyright: ignore [reportOptionalMemberAccess]


def test_session_rollback():
    """Test session rollback on error"""
    session = next(get_session())
    project = ProjectTable(name="Test Project", organization_uuid=ORGANIZATION_UUID)
    session.add(project)

    try:
        # Force an error by adding duplicate project
        duplicate = ProjectTable(
            name="Test Project", organization_uuid=ORGANIZATION_UUID
        )
        session.add(duplicate)
        session.commit()
    except Exception:
        session.rollback()

    # Verify original project was not committed
    stmt = select(ProjectTable)
    result = session.exec(stmt).all()
    assert len(result) == 0


def test_standalone_session():
    """Test standalone session context manager"""
    # Test normal operation
    with standalone_session() as session:
        assert isinstance(session, Session)

        # Add a project
        project = ProjectTable(
            name="Standalone Test", organization_uuid=ORGANIZATION_UUID
        )
        session.add(project)
        session.commit()

        # Verify project was committed
        stmt = select(ProjectTable).where(ProjectTable.name == "Standalone Test")
        result = session.exec(stmt).first()
        assert result is not None
        assert result.name == "Standalone Test"


def test_standalone_session_no_auto_commit():
    """Test that standalone session doesn't auto-commit"""
    with standalone_session() as session:
        # Add a project but don't commit
        project = ProjectTable(
            name="No Commit Test", organization_uuid=ORGANIZATION_UUID
        )
        session.add(project)
        # Exit without commit

    # Verify project was not saved
    with standalone_session() as session:
        stmt = select(ProjectTable).where(ProjectTable.name == "No Commit Test")
        result = session.exec(stmt).first()
        assert result is None


def test_standalone_session_rollback_on_error():
    """Test standalone session rollback on error"""
    with pytest.raises(RuntimeError), standalone_session() as session:
        # Add a project
        project = ProjectTable(
            name="Rollback Test", organization_uuid=ORGANIZATION_UUID
        )
        session.add(project)
        session.commit()

        # Add another project but raise error before commit
        project2 = ProjectTable(
            name="Rollback Test 2", organization_uuid=ORGANIZATION_UUID
        )
        session.add(project2)
        raise RuntimeError("Test error")

    # Verify first project was committed (committed changes are not rolled back)
    with standalone_session() as session:
        stmt = select(ProjectTable).where(ProjectTable.name == "Rollback Test")
        result = session.exec(stmt).first()
        assert result is not None

        # Verify second project was not committed
        stmt2 = select(ProjectTable).where(ProjectTable.name == "Rollback Test 2")
        result2 = session.exec(stmt2).first()
        assert result2 is None


def test_standalone_session_partial_commits():
    """Test standalone session with partial commits for batch processing"""
    with standalone_session() as session:
        # Simulate batch processing with partial commits
        for i in range(3):
            project = ProjectTable(
                name=f"Batch Item {i}", organization_uuid=ORGANIZATION_UUID
            )
            session.add(project)

            if i == 1:
                # Commit after second item
                session.commit()

        # Exit without committing the third item

    # Verify only first two items were saved
    with standalone_session() as session:
        stmt = select(ProjectTable).where(ProjectTable.name.like("Batch Item %"))  # pyright: ignore
        results = session.exec(stmt).all()
        assert len(results) == 2
        names = {r.name for r in results}
        assert "Batch Item 0" in names
        assert "Batch Item 1" in names
        assert "Batch Item 2" not in names
