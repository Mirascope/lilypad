"""Tests for the SpanService class"""

from uuid import uuid4

from sqlmodel import Session

from lilypad.server.models import (
    ProjectTable,
    Scope,
    SpanTable,
)
from lilypad.server.schemas.projects import ProjectPublic
from lilypad.server.schemas.users import UserPublic
from lilypad.server.services import SpanService


def test_find_records_by_version_uuid(
    db_session: Session, test_project: ProjectTable, test_user: UserPublic
):
    """Test finding spans by version uuid"""
    service = SpanService(db_session, test_user)
    function_uuid = uuid4()
    # Create test spans
    spans = [
        SpanTable(
            organization_uuid=test_project.organization_uuid,
            span_id=f"span_{i}",
            project_uuid=test_project.uuid,
            function_uuid=function_uuid,
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
    test_project_public = ProjectPublic.model_validate(test_project)
    # Test retrieval
    found_spans = service.find_records_by_function_uuid(
        test_project_public.uuid, function_uuid
    )
    assert len(found_spans) == 3
    assert all(span.function_uuid == function_uuid for span in found_spans)
