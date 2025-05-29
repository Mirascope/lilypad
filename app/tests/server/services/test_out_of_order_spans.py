"""Test out-of-order span handling at the service level."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session, func, select

from lilypad.server.models import (
    OrganizationTable,
    ProjectTable,
    SpanTable,
    UserTable,
)
from lilypad.server.models.spans import ParentStatus, Scope, SpanType
from lilypad.server.schemas.spans import SpanCreate
from lilypad.server.services.spans import SpanService


def create_test_span(
    span_id: str,
    trace_id: str,
    parent_span_id: str | None,
    name: str,
) -> SpanCreate:
    """Helper to create test span data."""
    now = datetime.now(timezone.utc)
    return SpanCreate(
        span_id=span_id,
        parent_span_id=parent_span_id,
        scope=Scope.LILYPAD,
        type=SpanType.FUNCTION,
        data={
            "span_id": span_id,
            "trace_id": trace_id,
            "parent_span_id": parent_span_id,
            "name": name,
            "start_time": now.timestamp(),
            "end_time": (now + timedelta(milliseconds=100)).timestamp(),
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
        name="Test Org for Spans",
        license="test-license",
    )
    db_session.add(org)
    
    user = UserTable(
        uuid=uuid.uuid4(),
        email="span-test@example.com",
        first_name="Span",
        last_name="Tester",
        active_organization_uuid=org.uuid,
    )
    db_session.add(user)
    db_session.commit()
    return org, user


@pytest.fixture
def test_project_for_spans(
    db_session: Session, test_org_and_user: tuple[OrganizationTable, UserTable]
) -> ProjectTable:
    """Create test project."""
    org, _ = test_org_and_user
    project = ProjectTable(
        uuid=uuid.uuid4(),
        name="Span Test Project",
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


def test_child_span_before_parent(
    db_session: Session,
    span_service: SpanService,
    test_project_for_spans: ProjectTable,
):
    """Test that child spans can be created before their parents."""
    trace_id = str(uuid.uuid4())
    parent_span_id = str(uuid.uuid4())
    child_span_id = str(uuid.uuid4())
    
    # Create child span first (parent doesn't exist)
    child_create = create_test_span(
        span_id=child_span_id,
        trace_id=trace_id,
        parent_span_id=parent_span_id,  # Parent doesn't exist yet
        name="Child Operation",
    )
    
    # This should succeed even though parent doesn't exist
    span_service.create_bulk_records(
        [child_create], 
        billing_service=None,
        project_uuid=test_project_for_spans.uuid,
        organization_uuid=test_project_for_spans.organization_uuid,
    )
    
    # Verify child was created with PENDING status
    child_span = db_session.exec(
        select(SpanTable).where(SpanTable.span_id == child_span_id)
    ).first()
    assert child_span is not None
    assert child_span.parent_status == ParentStatus.PENDING
    assert child_span.parent_span_id == parent_span_id  # Can reference parent directly now
    
    # Now create the parent
    parent_create = create_test_span(
        span_id=parent_span_id,
        trace_id=trace_id,
        parent_span_id=None,  # Root span
        name="Parent Operation",
    )
    
    span_service.create_bulk_records(
        [parent_create],
        billing_service=None,
        project_uuid=test_project_for_spans.uuid,
        organization_uuid=test_project_for_spans.organization_uuid,
    )
    
    # Verify parent was created successfully
    parent_span = db_session.exec(
        select(SpanTable).where(SpanTable.span_id == parent_span_id)
    ).first()
    assert parent_span is not None
    assert parent_span.parent_status == ParentStatus.RESOLVED
    
    # Child span should now be RESOLVED since parent was created
    # and resolve_pending_children was called
    db_session.refresh(child_span)
    assert child_span.parent_status == ParentStatus.RESOLVED
    assert child_span.parent_span_id == parent_span_id  # Relationship works!


def test_multiple_pending_children(
    db_session: Session,
    span_service: SpanService,
    test_project_for_spans: ProjectTable,
):
    """Test multiple children waiting for the same parent."""
    trace_id = str(uuid.uuid4())
    parent_span_id = str(uuid.uuid4())
    child_ids = [str(uuid.uuid4()) for _ in range(3)]
    
    # Create multiple children before parent
    child_creates = []
    for child_id in child_ids:
        child_create = SpanCreate(
            span_id=child_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            name=f"Child {child_id[:8]}",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            scope=Scope.LILYPAD,
            type=SpanType.FUNCTION,
                attributes={},
            events=[],
            links=[],
            resource={"attributes": {"service.name": "test"}},
            instrumentation_scope={"name": "lilypad", "version": "1.0.0"},
            data={},
        )
        child_creates.append(child_create)
    
    span_service.create_bulk_records(
        child_creates,
        billing_service=None,
        project_uuid=test_project_for_spans.uuid,
        organization_uuid=test_project_for_spans.organization_uuid,
    )
    
    # Verify all children are pending and can reference parent directly
    for child_id in child_ids:
        child_span = db_session.exec(
            select(SpanTable).where(SpanTable.span_id == child_id)
        ).first()
        assert child_span is not None
        assert child_span.parent_status == ParentStatus.PENDING
        assert child_span.parent_span_id == parent_span_id  # Direct reference works!
    
    # Create parent
    parent_create = SpanCreate(
        span_id=parent_span_id,
        trace_id=trace_id,
        parent_span_id=None,
        name="Parent Operation",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        scope=Scope.LILYPAD,
        type=SpanType.FUNCTION,
        attributes={},
        events=[],
        links=[],
        resource={"attributes": {"service.name": "test"}},
        instrumentation_scope={"name": "lilypad", "version": "1.0.0"},
        data={},
    )
    
    span_service.create_bulk_records(
        [parent_create],
        billing_service=None,
        project_uuid=test_project_for_spans.uuid,
        organization_uuid=test_project_for_spans.organization_uuid,
    )
    
    # Verify parent was created and children still reference it correctly
    parent_span = db_session.exec(
        select(SpanTable).where(SpanTable.span_id == parent_span_id)
    ).first()
    assert parent_span is not None
    assert parent_span.parent_status == ParentStatus.RESOLVED
    
    # Children should now be RESOLVED since parent was created
    for child_id in child_ids:
        child_span = db_session.exec(
            select(SpanTable).where(SpanTable.span_id == child_id)
        ).first()
        db_session.refresh(child_span)
        assert child_span.parent_status == ParentStatus.RESOLVED
        assert child_span.parent_span_id == parent_span_id  # Relationship works!


def test_nested_out_of_order_spans(
    db_session: Session,
    span_service: SpanService,
    test_project_for_spans: ProjectTable,
):
    """Test deeply nested spans arriving out of order."""
    trace_id = str(uuid.uuid4())
    
    # Create span IDs for: root -> level1 -> level2 -> level3
    root_id = str(uuid.uuid4())
    level1_id = str(uuid.uuid4())
    level2_id = str(uuid.uuid4())
    level3_id = str(uuid.uuid4())
    
    # Create spans in reverse order (deepest first)
    spans_data = [
        (level3_id, level2_id, "Level 3"),
        (level2_id, level1_id, "Level 2"),
        (level1_id, root_id, "Level 1"),
        (root_id, None, "Root"),
    ]
    
    for span_id, parent_id, name in spans_data:
        span_create = SpanCreate(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_id,
            name=name,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            scope=Scope.LILYPAD,
            type=SpanType.FUNCTION,
                attributes={},
            events=[],
            links=[],
            resource={"attributes": {"service.name": "test"}},
            instrumentation_scope={"name": "lilypad", "version": "1.0.0"},
            data={},
        )
        
        span_service.create_bulk_records(
        [span_create],
        billing_service=None,
        project_uuid=test_project_for_spans.uuid,
        organization_uuid=test_project_for_spans.organization_uuid,
    )
    
    # Check final state - all spans should be resolved since parents were created
    all_span_ids = [level3_id, level2_id, level1_id, root_id]
    for span_id in all_span_ids:
        span = db_session.exec(
            select(SpanTable).where(SpanTable.span_id == span_id)
        ).first()
        db_session.refresh(span)
        assert span is not None
        # All spans should be RESOLVED since we created them in order
        # and resolve_pending_children is called after each parent is created
        assert span.parent_status == ParentStatus.RESOLVED
    
    # Verify parent relationships
    level3 = db_session.exec(
        select(SpanTable).where(SpanTable.span_id == level3_id)
    ).first()
    assert level3.parent_span_id == level2_id
    
    level2 = db_session.exec(
        select(SpanTable).where(SpanTable.span_id == level2_id)
    ).first()
    assert level2.parent_span_id == level1_id
    
    level1 = db_session.exec(
        select(SpanTable).where(SpanTable.span_id == level1_id)
    ).first()
    assert level1.parent_span_id == root_id
    
    root = db_session.exec(
        select(SpanTable).where(SpanTable.span_id == root_id)
    ).first()
    assert root.parent_span_id is None


def test_orphaned_span_cleanup(
    db_session: Session,
    span_service: SpanService,
    test_project_for_spans: ProjectTable,
):
    """Test cleanup of orphaned spans."""
    trace_id = str(uuid.uuid4())
    orphan_span_id = str(uuid.uuid4())
    missing_parent_id = str(uuid.uuid4())
    
    # Create a span with a parent that will never arrive
    orphan_create = SpanCreate(
        span_id=orphan_span_id,
        trace_id=trace_id,
        parent_span_id=missing_parent_id,
        name="Orphaned Span",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        scope=Scope.LILYPAD,
        type=SpanType.FUNCTION,
        attributes={},
        events=[],
        links=[],
        resource={"attributes": {"service.name": "test"}},
        instrumentation_scope={"name": "lilypad", "version": "1.0.0"},
        data={},
    )
    
    span_service.create_bulk_records(
        [orphan_create],
        billing_service=None,
        project_uuid=test_project_for_spans.uuid,
        organization_uuid=test_project_for_spans.organization_uuid,
    )
    
    # Verify it's pending
    orphan = db_session.exec(
        select(SpanTable).where(SpanTable.span_id == orphan_span_id)
    ).first()
    assert orphan.parent_status == ParentStatus.PENDING
    
    # Run cleanup (with very short max_age for testing)
    cleaned_count = span_service.cleanup_orphaned_spans(max_age_hours=0)
    assert cleaned_count == 1
    
    # Verify it's now orphaned
    db_session.refresh(orphan)
    assert orphan.parent_status == ParentStatus.ORPHANED
    # In simplified approach, we might keep the parent_span_id for debugging
    # The important thing is that parent_status changed to ORPHANED
    
    
def test_span_status_counts(
    db_session: Session,
    span_service: SpanService,
    test_project_for_spans: ProjectTable,
):
    """Test that status counts are accurate."""
    trace_id = str(uuid.uuid4())
    
    # Create some resolved spans
    for i in range(3):
        span_create = SpanCreate(
            span_id=str(uuid.uuid4()),
            trace_id=trace_id,
            parent_span_id=None,
            name=f"Resolved {i}",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            scope=Scope.LILYPAD,
            type=SpanType.FUNCTION,
                attributes={},
            events=[],
            links=[],
            resource={"attributes": {"service.name": "test"}},
            instrumentation_scope={"name": "lilypad", "version": "1.0.0"},
            data={},
        )
        span_service.create_bulk_records(
        [span_create],
        billing_service=None,
        project_uuid=test_project_for_spans.uuid,
        organization_uuid=test_project_for_spans.organization_uuid,
    )
    
    # Create some pending spans
    missing_parent = str(uuid.uuid4())
    for i in range(2):
        span_create = SpanCreate(
            span_id=str(uuid.uuid4()),
            trace_id=trace_id,
            parent_span_id=missing_parent,
            name=f"Pending {i}",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            scope=Scope.LILYPAD,
            type=SpanType.FUNCTION,
                attributes={},
            events=[],
            links=[],
            resource={"attributes": {"service.name": "test"}},
            instrumentation_scope={"name": "lilypad", "version": "1.0.0"},
            data={},
        )
        span_service.create_bulk_records(
        [span_create],
        billing_service=None,
        project_uuid=test_project_for_spans.uuid,
        organization_uuid=test_project_for_spans.organization_uuid,
    )
    
    # Get counts
    resolved_count = db_session.exec(
        select(func.count()).where(
            SpanTable.project_uuid == test_project_for_spans.uuid,
            SpanTable.parent_status == ParentStatus.RESOLVED,
        )
    ).one()
    
    pending_count = db_session.exec(
        select(func.count()).where(
            SpanTable.project_uuid == test_project_for_spans.uuid,
            SpanTable.parent_status == ParentStatus.PENDING,
        )
    ).one()
    
    assert resolved_count == 3
    assert pending_count == 2