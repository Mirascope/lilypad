"""Pytest configuration for FastAPI services tests."""

from uuid import UUID

import pytest
from sqlmodel import Session

from lilypad.server.models import ProjectTable

ORGANIZATION_UUID = UUID("12345678-1234-1234-1234-123456789abc")


@pytest.fixture
def test_project(db_session: Session) -> ProjectTable:
    """Create test project."""
    project = ProjectTable(name="Test Project", organization_uuid=ORGANIZATION_UUID)
    db_session.add(project)
    db_session.commit()
    return project
