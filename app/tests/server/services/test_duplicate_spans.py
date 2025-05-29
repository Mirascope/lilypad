"""Test duplicate span handling."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlmodel import Session, select

from lilypad.server.models import (
    OrganizationTable,
    ProjectTable,
    SpanTable,
    UserTable,
)
from lilypad.server.models.spans import Scope, SpanType
from lilypad.server.schemas.spans import SpanCreate
from lilypad.server.services.spans import SpanService


def create_test_span(span_id: str, name: str) -> SpanCreate:
    """Helper to create test span data."""
    now = datetime.now(timezone.utc)
    return SpanCreate(
        span_id=span_id,
        parent_span_id=None,
        scope=Scope.LILYPAD,
        type=SpanType.FUNCTION,
        data={
            "span_id": span_id,
            "trace_id": str(uuid.uuid4()),
            "parent_span_id": None,
            "name": name,
            "start_time": now.timestamp(),
            "end_time": now.timestamp(),
            "attributes": {},
            "events": [],
            "links": [],
            "resource": {"attributes": {"service.name": "test"}},
            "instrumentation_scope": {"name": "lilypad", "version": "1.0.0"},
        },
        duration_ms=100,
    )


@pytest.fixture
def test_org_and_user(db_session: Session) -> tuple[OrganizationTable, UserTable]:
    """Create test organization and user."""
    org = OrganizationTable(
        uuid=uuid.uuid4(),
        name="Test Org for Duplicate Spans",
        license="test-license",
    )
    db_session.add(org)
    
    user = UserTable(
        uuid=uuid.uuid4(),
        email="duplicate-test@example.com",
        first_name="Duplicate",
        last_name="Tester",
        active_organization_uuid=org.uuid,
    )
    db_session.add(user)
    db_session.commit()
    return org, user


@pytest.fixture
def test_project_for_duplicates(
    db_session: Session, test_org_and_user: tuple[OrganizationTable, UserTable]
) -> ProjectTable:
    """Create test project."""
    org, _ = test_org_and_user
    project = ProjectTable(
        uuid=uuid.uuid4(),
        name="Duplicate Test Project",
        organization_uuid=org.uuid,
    )
    db_session.add(project)
    db_session.commit()
    return project


@pytest.fixture
def span_service(
    db_session: Session,
    test_org_and_user: tuple[OrganizationTable, UserTable],
) -> SpanService:
    """Create span service."""
    org, user = test_org_and_user
    from lilypad.server.schemas.users import UserPublic
    user_public = UserPublic.model_validate(user)
    return SpanService(db_session, user_public)


def test_duplicate_span_handling(
    db_session: Session,
    span_service: SpanService,
    test_project_for_duplicates: ProjectTable,
):
    """Test that duplicate spans are handled gracefully."""
    span_id = str(uuid.uuid4())
    
    # Create the same span twice
    span1 = create_test_span(span_id, "Test Span")
    span2 = create_test_span(span_id, "Test Span Duplicate")  # Same span_id!
    
    # First insertion should succeed
    result1 = span_service.create_bulk_records(
        [span1],
        billing_service=None,
        project_uuid=test_project_for_duplicates.uuid,
        organization_uuid=test_project_for_duplicates.organization_uuid,
    )
    assert len(result1) == 1
    assert result1[0].span_id == span_id
    
    # Second insertion should be gracefully skipped
    result2 = span_service.create_bulk_records(
        [span2],
        billing_service=None,
        project_uuid=test_project_for_duplicates.uuid,
        organization_uuid=test_project_for_duplicates.organization_uuid,
    )
    assert len(result2) == 0  # No new spans added
    
    # Verify only one span exists in database
    spans = db_session.exec(
        select(SpanTable).where(SpanTable.span_id == span_id)
    ).all()
    assert len(spans) == 1


def test_mixed_duplicate_and_new_spans(
    db_session: Session,
    span_service: SpanService,
    test_project_for_duplicates: ProjectTable,
):
    """Test handling mix of duplicate and new spans."""
    span_id1 = str(uuid.uuid4())
    span_id2 = str(uuid.uuid4())
    
    # First batch: create two spans
    span1 = create_test_span(span_id1, "Span 1")
    span2 = create_test_span(span_id2, "Span 2")
    
    result1 = span_service.create_bulk_records(
        [span1, span2],
        billing_service=None,
        project_uuid=test_project_for_duplicates.uuid,
        organization_uuid=test_project_for_duplicates.organization_uuid,
    )
    assert len(result1) == 2
    
    # Second batch: one duplicate, one new
    span1_dup = create_test_span(span_id1, "Span 1 Duplicate")  # Duplicate
    span3 = create_test_span(str(uuid.uuid4()), "Span 3")       # New
    
    result2 = span_service.create_bulk_records(
        [span1_dup, span3],
        billing_service=None,
        project_uuid=test_project_for_duplicates.uuid,
        organization_uuid=test_project_for_duplicates.organization_uuid,
    )
    assert len(result2) == 1  # Only the new span was added
    assert result2[0].data["name"] == "Span 3"
    
    # Verify total spans in database
    total_spans = db_session.exec(
        select(SpanTable).where(
            SpanTable.project_uuid == test_project_for_duplicates.uuid
        )
    ).all()
    assert len(total_spans) == 3  # span1, span2, span3


def test_all_duplicates_batch(
    db_session: Session,
    span_service: SpanService,
    test_project_for_duplicates: ProjectTable,
):
    """Test handling batch where all spans are duplicates."""
    span_id1 = str(uuid.uuid4())
    span_id2 = str(uuid.uuid4())
    
    # First batch: create spans
    spans = [
        create_test_span(span_id1, "Span 1"),
        create_test_span(span_id2, "Span 2"),
    ]
    
    result1 = span_service.create_bulk_records(
        spans,
        billing_service=None,
        project_uuid=test_project_for_duplicates.uuid,
        organization_uuid=test_project_for_duplicates.organization_uuid,
    )
    assert len(result1) == 2
    
    # Second batch: all duplicates
    duplicate_spans = [
        create_test_span(span_id1, "Span 1 Dup"),
        create_test_span(span_id2, "Span 2 Dup"),
    ]
    
    result2 = span_service.create_bulk_records(
        duplicate_spans,
        billing_service=None,
        project_uuid=test_project_for_duplicates.uuid,
        organization_uuid=test_project_for_duplicates.organization_uuid,
    )
    assert len(result2) == 0  # All were duplicates, nothing added