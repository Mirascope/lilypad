"""Tests for the comments service."""

import pytest
from sqlmodel import Session
from uuid import uuid4

from lilypad.server.models.comments import CommentTable
from lilypad.server.schemas.comments import CommentCreate
from lilypad.server.schemas.users import UserPublic
from lilypad.server.services.comments import CommentService


@pytest.fixture
def comment_service(db_session: Session, test_user: UserPublic) -> CommentService:
    """Create a CommentService instance."""
    return CommentService(session=db_session, user=test_user)


@pytest.fixture
def test_comment(comment_service: CommentService, db_session: Session) -> CommentTable:
    """Create a test comment."""
    span_uuid = uuid4()
    comment_data = CommentCreate(
        span_uuid=span_uuid,
        text="Test comment content"
    )
    comment = comment_service.create_record(comment_data, user_uuid=comment_service.user.uuid)
    db_session.commit()
    db_session.refresh(comment)
    return comment


def test_find_by_spans_with_comments(
    comment_service: CommentService,
    test_comment: CommentTable,
    db_session: Session
):
    """Test finding comments by span UUID."""
    # Find comments for the span
    found_comments = comment_service.find_by_spans(test_comment.span_uuid)
    
    # Should find the test comment
    assert len(found_comments) >= 1
    assert any(comment.uuid == test_comment.uuid for comment in found_comments)
    
    # All comments should belong to the same span
    for comment in found_comments:
        assert comment.span_uuid == test_comment.span_uuid
        assert comment.organization_uuid == comment_service.user.active_organization_uuid


def test_find_by_spans_no_comments(comment_service: CommentService):
    """Test finding comments for span with no comments."""
    span_uuid = uuid4()
    
    # Find comments for span with no comments
    found_comments = comment_service.find_by_spans(span_uuid)
    
    # Should return empty list
    assert len(found_comments) == 0


def test_find_by_spans_multiple_comments_ordered(
    comment_service: CommentService,
    db_session: Session
):
    """Test that comments are returned in created_at order (ascending)."""
    span_uuid = uuid4()
    
    # Create multiple comments for the same span
    comment1_data = CommentCreate(
        span_uuid=span_uuid,
        text="First comment"
    )
    comment1 = comment_service.create_record(comment1_data, user_uuid=comment_service.user.uuid)
    db_session.flush()
    
    comment2_data = CommentCreate(
        span_uuid=span_uuid,
        text="Second comment"
    )
    comment2 = comment_service.create_record(comment2_data, user_uuid=comment_service.user.uuid)
    db_session.flush()
    
    comment3_data = CommentCreate(
        span_uuid=span_uuid,
        text="Third comment"
    )
    comment3 = comment_service.create_record(comment3_data, user_uuid=comment_service.user.uuid)
    db_session.commit()
    
    # Find all comments for the span
    found_comments = comment_service.find_by_spans(span_uuid)
    
    # Should have all 3 comments
    assert len(found_comments) == 3
    
    # Should be ordered by created_at (ascending)
    # First comment should be first in the list
    assert found_comments[0].uuid == comment1.uuid
    assert found_comments[1].uuid == comment2.uuid
    assert found_comments[2].uuid == comment3.uuid
    
    # Verify the ordering is correct by checking timestamps
    for i in range(len(found_comments) - 1):
        assert found_comments[i].created_at <= found_comments[i + 1].created_at


def test_find_by_spans_organization_filter(
    comment_service: CommentService,
    db_session: Session
):
    """Test that find_by_spans only returns comments from the user's organization."""
    span_uuid = uuid4()
    
    # Create a comment in the user's organization
    comment_data = CommentCreate(
        span_uuid=span_uuid,
        text="User organization comment"
    )
    user_comment = comment_service.create_record(comment_data, user_uuid=comment_service.user.uuid)
    db_session.commit()
    
    # Create a comment with a different organization UUID directly in the database
    # (simulating a comment from another organization)
    other_org_uuid = uuid4()
    other_comment = CommentTable(
        span_uuid=span_uuid,
        text="Other organization comment",
        organization_uuid=other_org_uuid,
        user_uuid=comment_service.user.uuid  # Same user but different org
    )
    db_session.add(other_comment)
    db_session.commit()
    
    # Find comments - should only return the user's organization comment
    found_comments = comment_service.find_by_spans(span_uuid)
    
    # Should only find the comment from user's organization
    assert len(found_comments) == 1
    assert found_comments[0].uuid == user_comment.uuid
    assert found_comments[0].organization_uuid == comment_service.user.active_organization_uuid


def test_create_record_adds_organization(
    comment_service: CommentService,
    db_session: Session
):
    """Test that create_record automatically adds organization_uuid."""
    span_uuid = uuid4()
    
    # Create a comment
    comment_data = CommentCreate(
        span_uuid=span_uuid,
        text="Test comment for organization"
    )
    created_comment = comment_service.create_record(comment_data, user_uuid=comment_service.user.uuid)
    
    # Should have organization_uuid set from the user
    assert created_comment.organization_uuid == comment_service.user.active_organization_uuid
    assert created_comment.span_uuid == span_uuid
    assert created_comment.text == "Test comment for organization"
    assert created_comment.uuid is not None


def test_comment_service_inheritance(comment_service: CommentService):
    """Test that CommentService properly inherits from BaseOrganizationService."""
    # Should have all BaseOrganizationService attributes
    assert hasattr(comment_service, 'session')
    assert hasattr(comment_service, 'user')
    assert hasattr(comment_service, 'table')
    assert hasattr(comment_service, 'create_model')
    
    # Should have inherited methods
    assert hasattr(comment_service, 'find_record')
    assert hasattr(comment_service, 'find_record_by_uuid')
    assert hasattr(comment_service, 'find_all_records')
    assert hasattr(comment_service, 'delete_record_by_uuid')
    assert hasattr(comment_service, 'update_record_by_uuid')
    
    # Check service configuration
    assert comment_service.table == CommentTable
    assert comment_service.create_model == CommentCreate


def test_find_by_spans_with_different_spans(
    comment_service: CommentService,
    db_session: Session
):
    """Test that find_by_spans only returns comments for the specified span."""
    span1_uuid = uuid4()
    span2_uuid = uuid4()
    
    # Create comments for different spans
    comment1_data = CommentCreate(
        span_uuid=span1_uuid,
        text="Comment for span 1"
    )
    comment1 = comment_service.create_record(comment1_data, user_uuid=comment_service.user.uuid)
    
    comment2_data = CommentCreate(
        span_uuid=span2_uuid,
        text="Comment for span 2"
    )
    comment2 = comment_service.create_record(comment2_data, user_uuid=comment_service.user.uuid)
    db_session.commit()
    
    # Find comments for span 1
    span1_comments = comment_service.find_by_spans(span1_uuid)
    assert len(span1_comments) == 1
    assert span1_comments[0].uuid == comment1.uuid
    assert span1_comments[0].span_uuid == span1_uuid
    
    # Find comments for span 2
    span2_comments = comment_service.find_by_spans(span2_uuid)
    assert len(span2_comments) == 1
    assert span2_comments[0].uuid == comment2.uuid
    assert span2_comments[0].span_uuid == span2_uuid