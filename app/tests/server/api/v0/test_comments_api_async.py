"""Async tests for comments API."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from lilypad.server.models import CommentTable, ProjectTable, SpanTable, UserTable
from lilypad.server.models.spans import Scope
from tests.async_test_utils import (
    AsyncDatabaseTestMixin,
    AsyncTestFactory,
    fix_timezone_for_sqlite,
)


class TestCommentsAPIAsync(AsyncDatabaseTestMixin):
    """Test comments API endpoints asynchronously."""

    @pytest_asyncio.fixture
    async def test_span(
        self, async_session: AsyncSession, async_test_project: ProjectTable
    ) -> SpanTable:
        """Create a test span for comments."""
        factory = AsyncTestFactory(async_session)
        span = await factory.create(
            SpanTable,
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
            project_uuid=async_test_project.uuid,
            organization_uuid=async_test_project.organization_uuid,
        )
        return span

    @pytest_asyncio.fixture
    async def test_comment(
        self,
        async_session: AsyncSession,
        test_span: SpanTable,
        async_test_user: UserTable,
    ) -> CommentTable:
        """Create a test comment."""
        factory = AsyncTestFactory(async_session)
        now_utc = datetime.now(timezone.utc)
        comment = await factory.create(
            CommentTable,
            text="Test comment",
            span_uuid=test_span.uuid,
            user_uuid=async_test_user.uuid,
            organization_uuid=test_span.organization_uuid,
            created_at=now_utc,
            updated_at=now_utc,
        )
        return fix_timezone_for_sqlite(comment)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_comments_empty(self, async_client: AsyncClient):
        """Test getting comments when none exist."""
        response = await async_client.get("/comments")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_comments_with_data(
        self,
        async_client: AsyncClient,
        test_comment: CommentTable,
        async_session: AsyncSession,
    ):
        """Test getting comments with existing data."""
        # Ensure data is committed
        await async_session.commit()

        response = await async_client.get("/comments")
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

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_comments_by_span(
        self,
        async_client: AsyncClient,
        test_span: SpanTable,
        test_comment: CommentTable,
    ):
        """Test getting comments by span UUID."""
        response = await async_client.get(f"/spans/{test_span.uuid}/comments")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["text"] == "Test comment"
        assert data[0]["span_uuid"] == str(test_span.uuid)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_comments_by_span_empty(
        self,
        async_client: AsyncClient,
        test_span: SpanTable,
        async_session: AsyncSession,
    ):
        """Test getting comments by span when none exist."""
        # Create a new span without comments
        factory = AsyncTestFactory(async_session)
        new_span = await factory.create(
            SpanTable,
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

        response = await async_client.get(f"/spans/{new_span.uuid}/comments")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_comment_by_uuid(
        self, async_client: AsyncClient, test_comment: CommentTable
    ):
        """Test getting a specific comment by UUID."""
        response = await async_client.get(f"/comments/{test_comment.uuid}")
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == str(test_comment.uuid)
        assert data["text"] == "Test comment"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_comment_not_found(self, async_client: AsyncClient):
        """Test getting a comment with invalid UUID."""
        fake_uuid = uuid4()
        response = await async_client.get(f"/comments/{fake_uuid}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_create_comment(
        self, async_client: AsyncClient, test_span: SpanTable
    ):
        """Test creating a new comment."""
        comment_data = {
            "text": "New test comment",
            "span_uuid": str(test_span.uuid),
        }
        response = await async_client.post("/comments", json=comment_data)
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "New test comment"
        assert data["span_uuid"] == str(test_span.uuid)
        assert "uuid" in data
        assert "created_at" in data
        assert data["is_edited"] is False

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_update_comment(
        self, async_client: AsyncClient, test_comment: CommentTable
    ):
        """Test updating a comment."""
        update_data = {
            "text": "Updated comment text",
        }
        response = await async_client.patch(
            f"/comments/{test_comment.uuid}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Updated comment text"
        assert data["is_edited"] is True

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_update_comment_not_found(self, async_client: AsyncClient):
        """Test updating a non-existent comment."""
        fake_uuid = uuid4()
        update_data = {"text": "Updated text"}
        response = await async_client.patch(f"/comments/{fake_uuid}", json=update_data)
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_delete_comment(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        test_span: SpanTable,
        async_test_user: UserTable,
    ):
        """Test deleting a comment."""
        # Create a comment to delete
        factory = AsyncTestFactory(async_session)
        comment_to_delete = await factory.create(
            CommentTable,
            text="To be deleted",
            span_uuid=test_span.uuid,
            user_uuid=async_test_user.uuid,
            organization_uuid=test_span.organization_uuid,
        )

        response = await async_client.delete(f"/comments/{comment_to_delete.uuid}")
        assert response.status_code == 200
        assert response.json() is True

        # Verify it's deleted
        response = await async_client.get(f"/comments/{comment_to_delete.uuid}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_delete_comment_not_found(self, async_client: AsyncClient):
        """Test deleting a non-existent comment."""
        fake_uuid = uuid4()
        response = await async_client.delete(f"/comments/{fake_uuid}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_create_comment_integrity_error(
        self, async_client: AsyncClient, test_span: SpanTable
    ):
        """Test creating a comment with integrity error."""
        # This test would need to trigger an IntegrityError
        # Since comments don't have unique constraints, we'll test with invalid data
        comment_data = {
            "text": None,  # This should fail validation before IntegrityError
            "span_uuid": str(test_span.uuid),
        }
        response = await async_client.post("/comments", json=comment_data)
        # Should fail with validation error (422) not IntegrityError
        assert response.status_code == 422
