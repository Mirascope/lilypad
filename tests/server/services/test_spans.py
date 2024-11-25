"""Tests for the SpanService class"""

import pytest
from sqlmodel import Session

from lilypad.server.models import ProjectTable, Scope, SpanTable
from lilypad.server.services import SpanService


@pytest.fixture
def test_project(db_session: Session) -> ProjectTable:
    """Create test project"""
    project = ProjectTable(name="Test Project")
    db_session.add(project)
    db_session.commit()
    return project


def test_find_records_by_version_id(db_session: Session, test_project: ProjectTable):
    """Test finding spans by version ID"""
    service = SpanService(db_session)

    # Create test spans
    spans = [
        SpanTable(
            id=f"span_{i}",
            project_id=test_project.id,
            version_id=1,
            scope=Scope.LILYPAD,
            data={
                "attributes": {
                    "lilypad.function_name": "test_func",
                }
            },
        )
        for i in range(3)
    ]

    db_session.add_all(spans)
    db_session.commit()

    # Test retrieval
    found_spans = service.find_records_by_version_id(test_project.id, 1)
    assert len(found_spans) == 3
    assert all(span.version_id == 1 for span in found_spans)
