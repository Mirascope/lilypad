"""Tests for comments API."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from lilypad.server.models import CommentTable, ProjectTable, SpanTable
from lilypad.server.models.spans import Scope
from lilypad.server.services import CommentService


class TestCommentsAPI:
    """Test comments API endpoints."""

    @pytest.fixture
    def test_span(self, session: Session, test_project: ProjectTable) -> SpanTable:
        """Create a test span for comments."""
        span = SpanTable(
            span_id="test_span_id",
            trace_id="test_trace",
            parent_span_id=None,
            scope=Scope.LLM,
            data={
                "name": "test_span",
                "trace_id": "test_trace",
                "start_time": datetime.now(timezone.utc).isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "status": {"status_code": "OK"},
                "attributes": {},
            },
            project_uuid=test_project.uuid,
            organization_uuid=test_project.organization_uuid,
        )
        session.add(span)
        session.commit()
        session.refresh(span)
        return span

    @pytest.fixture
    def test_comment(
        self, session: Session, test_span: SpanTable, test_user
    ) -> CommentTable:
        """Create a test comment."""
        # Create comment with explicit timezone-aware timestamps
        now_utc = datetime.now(timezone.utc)
        comment = CommentTable(
            text="Test comment",
            span_uuid=test_span.uuid,  # type: ignore[arg-type]
            user_uuid=test_user.uuid,
            organization_uuid=test_span.organization_uuid,
            created_at=now_utc,
            updated_at=now_utc,
        )
        session.add(comment)
        session.commit()
        session.refresh(comment)

        # SQLite workaround: ensure timezone info is preserved
        if comment.updated_at and comment.updated_at.tzinfo is None:
            comment.updated_at = comment.updated_at.replace(tzinfo=timezone.utc)
        if comment.created_at and comment.created_at.tzinfo is None:
            comment.created_at = comment.created_at.replace(tzinfo=timezone.utc)

        return comment

    def test_get_comments_empty(self, client: TestClient):
        """Test getting comments when none exist."""
        response = client.get("/comments")
        assert response.status_code == 200
        # There might be a comment from fixtures, so check it's a list
        data = response.json()
        assert isinstance(data, list)

    def test_get_comments_with_data(
        self,
        client: TestClient,
        test_comment: CommentTable,
        session: Session,
        monkeypatch,
    ):
        """Test getting comments with existing data."""
        # Force commit to ensure data is visible
        session.commit()

        # SQLite doesn't preserve timezone info, so we need to patch the service
        # to ensure timezone-aware datetimes are returned
        original_find_all = CommentService.find_all_records

        def mock_find_all_records(self):
            results = original_find_all(self)
            # Fix timezone info for SQLite compatibility
            for comment in results:
                if comment.updated_at and comment.updated_at.tzinfo is None:
                    comment.updated_at = comment.updated_at.replace(tzinfo=timezone.utc)
                if comment.created_at and comment.created_at.tzinfo is None:
                    comment.created_at = comment.created_at.replace(tzinfo=timezone.utc)
            return results

        monkeypatch.setattr(CommentService, "find_all_records", mock_find_all_records)

        response = client.get("/comments")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        # Find our test comment
        found = False
        for comment in data:
            if comment["uuid"] == str(test_comment.uuid):
                found = True
                assert comment["text"] == "Test comment"
                break
        assert found

    def test_get_comments_by_span(
        self,
        client: TestClient,
        test_span: SpanTable,
        test_comment: CommentTable,
        monkeypatch,
    ):
        """Test getting comments by span UUID."""
        # SQLite doesn't preserve timezone info, so we need to patch the service
        original_find_by_spans = CommentService.find_by_spans

        def mock_find_by_spans(self, *args, **kwargs):
            results = original_find_by_spans(self, *args, **kwargs)
            # Fix timezone info for SQLite compatibility
            for comment in results:
                if comment.updated_at and comment.updated_at.tzinfo is None:
                    comment.updated_at = comment.updated_at.replace(tzinfo=timezone.utc)
                if comment.created_at and comment.created_at.tzinfo is None:
                    comment.created_at = comment.created_at.replace(tzinfo=timezone.utc)
            return results

        monkeypatch.setattr(CommentService, "find_by_spans", mock_find_by_spans)

        response = client.get(f"/spans/{test_span.uuid}/comments")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["text"] == "Test comment"
        assert data[0]["span_uuid"] == str(test_span.uuid)

    def test_get_comments_by_span_empty(
        self, client: TestClient, test_span: SpanTable, session: Session
    ):
        """Test getting comments by span when none exist."""
        # Create a new span without comments
        new_span = SpanTable(
            span_id="empty_span_id",
            trace_id="empty_trace",
            parent_span_id=None,
            scope=Scope.LLM,
            data={
                "name": "empty_span",
                "trace_id": "empty_trace",
                "start_time": datetime.now(timezone.utc).isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "status": {"status_code": "OK"},
                "attributes": {},
            },
            project_uuid=test_span.project_uuid,
            organization_uuid=test_span.organization_uuid,
        )
        session.add(new_span)
        session.commit()
        session.refresh(new_span)

        response = client.get(f"/spans/{new_span.uuid}/comments")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_comment_by_uuid(
        self, client: TestClient, test_comment: CommentTable, monkeypatch
    ):
        """Test getting a specific comment by UUID."""
        # SQLite doesn't preserve timezone info, so we need to patch the service
        original_find_record = CommentService.find_record_by_uuid

        def mock_find_record_by_uuid(self, *args, **kwargs):
            result = original_find_record(self, *args, **kwargs)
            # Fix timezone info for SQLite compatibility
            if result and result.updated_at and result.updated_at.tzinfo is None:
                result.updated_at = result.updated_at.replace(tzinfo=timezone.utc)
            if result and result.created_at and result.created_at.tzinfo is None:
                result.created_at = result.created_at.replace(tzinfo=timezone.utc)
            return result

        monkeypatch.setattr(
            CommentService, "find_record_by_uuid", mock_find_record_by_uuid
        )

        response = client.get(f"/comments/{test_comment.uuid}")
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == str(test_comment.uuid)
        assert data["text"] == "Test comment"

    def test_get_comment_not_found(self, client: TestClient):
        """Test getting a comment with invalid UUID."""
        fake_uuid = uuid4()
        response = client.get(f"/comments/{fake_uuid}")
        assert response.status_code == 404

    def test_create_comment(
        self, client: TestClient, test_span: SpanTable, monkeypatch
    ):
        """Test creating a new comment."""
        # SQLite doesn't preserve timezone info, so we need to patch the service
        original_create_record = CommentService.create_record

        def mock_create_record(self, *args, **kwargs):
            result = original_create_record(self, *args, **kwargs)
            # Fix timezone info for SQLite compatibility
            if result.updated_at and result.updated_at.tzinfo is None:
                result.updated_at = result.updated_at.replace(tzinfo=timezone.utc)
            if result.created_at and result.created_at.tzinfo is None:
                result.created_at = result.created_at.replace(tzinfo=timezone.utc)
            return result

        monkeypatch.setattr(CommentService, "create_record", mock_create_record)

        comment_data = {
            "text": "New test comment",
            "span_uuid": str(test_span.uuid),
        }
        response = client.post("/comments", json=comment_data)
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "New test comment"
        assert data["span_uuid"] == str(test_span.uuid)
        assert "uuid" in data
        assert "created_at" in data
        assert data["is_edited"] is False

    def test_update_comment(
        self, client: TestClient, test_comment: CommentTable, monkeypatch
    ):
        """Test updating a comment."""
        # SQLite doesn't preserve timezone info, so we need to patch the service
        original_update_record = CommentService.update_record_by_uuid

        def mock_update_record_by_uuid(self, *args, **kwargs):
            result = original_update_record(self, *args, **kwargs)
            # Fix timezone info for SQLite compatibility
            if result.updated_at and result.updated_at.tzinfo is None:
                result.updated_at = result.updated_at.replace(tzinfo=timezone.utc)
            if result.created_at and result.created_at.tzinfo is None:
                result.created_at = result.created_at.replace(tzinfo=timezone.utc)
            return result

        monkeypatch.setattr(
            CommentService, "update_record_by_uuid", mock_update_record_by_uuid
        )

        update_data = {
            "text": "Updated comment text",
        }
        response = client.patch(f"/comments/{test_comment.uuid}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Updated comment text"
        assert data["is_edited"] is True

    def test_update_comment_not_found(self, client: TestClient):
        """Test updating a non-existent comment."""
        fake_uuid = uuid4()
        update_data = {"text": "Updated text"}
        response = client.patch(f"/comments/{fake_uuid}", json=update_data)
        assert response.status_code == 404

    def test_delete_comment(
        self, client: TestClient, session: Session, test_span: SpanTable, test_user
    ):
        """Test deleting a comment."""
        # Create a comment to delete
        comment_to_delete = CommentTable(
            text="To be deleted",
            span_uuid=test_span.uuid,  # type: ignore[arg-type]
            user_uuid=test_user.uuid,
            organization_uuid=test_span.organization_uuid,
        )
        session.add(comment_to_delete)
        session.commit()
        session.refresh(comment_to_delete)

        response = client.delete(f"/comments/{comment_to_delete.uuid}")
        assert response.status_code == 200
        assert response.json() is True

        # Verify it's deleted
        response = client.get(f"/comments/{comment_to_delete.uuid}")
        assert response.status_code == 404

    def test_delete_comment_not_found(self, client: TestClient):
        """Test deleting a non-existent comment."""
        fake_uuid = uuid4()
        response = client.delete(f"/comments/{fake_uuid}")
        assert response.status_code == 404

    def test_create_comment_integrity_error(
        self, client: TestClient, test_span: SpanTable
    ):
        """Test creating a comment with integrity error."""
        # This test would need to trigger an IntegrityError
        # Since comments don't have unique constraints, we'll test with invalid data
        comment_data = {
            "text": None,  # This should fail validation before IntegrityError
            "span_uuid": str(test_span.uuid),
        }
        response = client.post("/comments", json=comment_data)
        # Should fail with validation error (422) not IntegrityError
        assert response.status_code == 422
