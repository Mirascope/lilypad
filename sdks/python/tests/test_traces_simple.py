"""
Focused unit tests for the trace bug fix and critical error handling.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from lilypad.traces import Trace, AsyncTrace
from lilypad.generated.types.paginated_span_public import PaginatedSpanPublic
from lilypad.generated.types.span_public import SpanPublic


class TestTraceBugFix:
    """Test the specific bug fix for iterating over response.items"""

    def test_get_span_uuid_success(self):
        """Test successful span UUID retrieval with correct response.items iteration"""
        # Create mock span
        mock_span = SpanPublic(
            span_id="00000000075bcd15",  # format_span_id(123456789)
            uuid_="test-span-uuid",
            project_uuid="test-project",
            scope="lilypad",
            annotations=[],
            child_spans=[],
            created_at=datetime.now(),
            tags=[],
        )

        # Create mock paginated response
        mock_response = PaginatedSpanPublic(items=[mock_span], limit=10, offset=0, total=1)

        # Create mock client
        mock_client = Mock()
        mock_client.projects.functions.spans.list_paginated.return_value = mock_response

        # Test the fix
        trace = Trace(response="test", span_id=123456789, function_uuid="test-func-uuid")
        result = trace._get_span_uuid(mock_client)

        assert result == "test-span-uuid"
        mock_client.projects.functions.spans.list_paginated.assert_called_once()

    def test_get_span_uuid_no_match(self):
        """Test that None is returned when no matching span is found"""
        # Create mock span with different span_id
        mock_span = SpanPublic(
            span_id="different-span-id",
            uuid_="test-span-uuid",
            project_uuid="test-project",
            scope="lilypad",
            annotations=[],
            child_spans=[],
            created_at=datetime.now(),
            tags=[],
        )

        mock_response = PaginatedSpanPublic(items=[mock_span], limit=10, offset=0, total=1)

        mock_client = Mock()
        mock_client.projects.functions.spans.list_paginated.return_value = mock_response

        trace = Trace(response="test", span_id=123456789, function_uuid="test-func-uuid")
        result = trace._get_span_uuid(mock_client)

        assert result is None

    def test_get_span_uuid_empty_response(self):
        """Test handling of empty response"""
        mock_response = PaginatedSpanPublic(items=[], limit=10, offset=0, total=0)

        mock_client = Mock()
        mock_client.projects.functions.spans.list_paginated.return_value = mock_response

        trace = Trace(response="test", span_id=123456789, function_uuid="test-func-uuid")
        result = trace._get_span_uuid(mock_client)

        assert result is None

    def test_get_span_uuid_multiple_spans(self):
        """Test finding the correct span when multiple spans exist"""
        # Create multiple mock spans
        mock_span1 = SpanPublic(
            span_id="different-span-id",
            uuid_="wrong-uuid",
            project_uuid="test-project",
            scope="lilypad",
            annotations=[],
            child_spans=[],
            created_at=datetime.now(),
            tags=[],
        )

        mock_span2 = SpanPublic(
            span_id="00000000075bcd15",  # format_span_id(123456789)
            uuid_="correct-uuid",
            project_uuid="test-project",
            scope="lilypad",
            annotations=[],
            child_spans=[],
            created_at=datetime.now(),
            tags=[],
        )

        mock_response = PaginatedSpanPublic(items=[mock_span1, mock_span2], limit=10, offset=0, total=2)

        mock_client = Mock()
        mock_client.projects.functions.spans.list_paginated.return_value = mock_response

        trace = Trace(response="test", span_id=123456789, function_uuid="test-func-uuid")
        result = trace._get_span_uuid(mock_client)

        assert result == "correct-uuid"

    @pytest.mark.asyncio
    async def test_async_get_span_uuid_success(self):
        """Test successful async span UUID retrieval"""
        # Create mock span
        mock_span = SpanPublic(
            span_id="00000000075bcd15",  # format_span_id(123456789)
            uuid_="test-span-uuid",
            project_uuid="test-project",
            scope="lilypad",
            annotations=[],
            child_spans=[],
            created_at=datetime.now(),
            tags=[],
        )

        mock_response = PaginatedSpanPublic(items=[mock_span], limit=10, offset=0, total=1)

        # Create mock async client with async return
        mock_client = Mock()

        async def mock_list_paginated(*args, **kwargs):
            return mock_response

        mock_client.projects.functions.spans.list_paginated = mock_list_paginated

        # Test the async fix
        trace = AsyncTrace(response="test", span_id=123456789, function_uuid="test-func-uuid")
        result = await trace._get_span_uuid(mock_client)

        assert result == "test-span-uuid"


class TestCriticalErrorCases:
    """Test critical error cases that need attention"""

    def test_assign_with_none_span_uuid_raises_span_not_found_error(self):
        """Fixed: assign() now raises SpanNotFoundError when span not found (instead of passing None to API)"""
        from lilypad.exceptions import SpanNotFoundError

        trace = Trace(response="test", span_id=123456789, function_uuid="test-func-uuid")

        # Mock to simulate span not found
        with patch.object(trace, "_get_span_uuid", return_value=None):
            # Now correctly raises SpanNotFoundError instead of passing None to API
            with pytest.raises(SpanNotFoundError) as exc_info:
                trace.assign("user@example.com")

            # Verify proper error message
            assert "Cannot assign: span not found" in str(exc_info.value)
            assert "test-func-uuid" in str(exc_info.value)

    def test_tag_with_none_span_uuid_raises_span_not_found_error(self):
        """Fixed: tag() now raises SpanNotFoundError when span not found (instead of passing None to API)"""
        from lilypad.exceptions import SpanNotFoundError

        trace = Trace(response="test", span_id=123456789, function_uuid="test-func-uuid")

        # Mock to simulate span not found
        with patch.object(trace, "_get_span_uuid", return_value=None):
            # Now correctly raises SpanNotFoundError instead of passing None to API
            with pytest.raises(SpanNotFoundError) as exc_info:
                trace.tag("tag1")

            # Verify proper error message
            assert "Cannot tag: span not found" in str(exc_info.value)
            assert "test-func-uuid" in str(exc_info.value)

    def test_annotate_with_none_span_uuid_raises_span_not_found_error(self):
        """Fixed: annotate() now raises SpanNotFoundError when span not found (instead of passing None to API)"""
        from lilypad.exceptions import SpanNotFoundError
        from lilypad.traces import Annotation

        trace = Trace(response="test", span_id=123456789, function_uuid="test-func-uuid")

        # Mock to simulate span not found
        with patch.object(trace, "_get_span_uuid", return_value=None):
            annotation = Annotation(data={"key": "value"}, label="pass", reasoning="test", type="manual")

            # Now correctly raises SpanNotFoundError instead of passing None to API
            with pytest.raises(SpanNotFoundError) as exc_info:
                trace.annotate(annotation)

            # Verify proper error message
            assert "Cannot annotate: span not found" in str(exc_info.value)
            assert "test-func-uuid" in str(exc_info.value)

    def test_flush_behavior_in_get_span_uuid(self):
        """Test that _force_flush is called when _flush is False"""
        trace = Trace(response="test", span_id=123456789, function_uuid="test-func-uuid")
        assert trace._flush is False  # Default state

        mock_response = PaginatedSpanPublic(items=[], limit=10, offset=0, total=0)
        mock_client = Mock()
        mock_client.projects.functions.spans.list_paginated.return_value = mock_response

        with patch.object(trace, "_force_flush") as mock_force_flush:
            trace._get_span_uuid(mock_client)

            # Verify _force_flush was called
            mock_force_flush.assert_called_once()

    def test_no_duplicate_flush_when_already_flushed(self):
        """Test that _force_flush is not called when already flushed"""
        trace = Trace(response="test", span_id=123456789, function_uuid="test-func-uuid")
        trace._flush = True  # Set as already flushed

        mock_response = PaginatedSpanPublic(items=[], limit=10, offset=0, total=0)
        mock_client = Mock()
        mock_client.projects.functions.spans.list_paginated.return_value = mock_response

        with patch.object(trace, "_force_flush") as mock_force_flush:
            trace._get_span_uuid(mock_client)

            # Verify _force_flush was NOT called
            mock_force_flush.assert_not_called()


class TestInputValidationIssues:
    """Test input validation issues that should be addressed"""

    def test_assign_with_empty_email_list(self):
        """Test assignment with no email addresses raises ValueError"""
        trace = Trace(response="test", span_id=123456789, function_uuid="test-func-uuid")

        # Empty email list should now raise ValueError with the critical fixes
        with pytest.raises(ValueError) as exc_info:
            trace.assign()

        assert "At least one email address must be provided" in str(exc_info.value)

    def test_tag_with_empty_tags_returns_early(self):
        """Test that tag() returns early when no tags provided"""
        trace = Trace(response="test", span_id=123456789, function_uuid="test-func-uuid")

        # Should not make any API calls when no tags provided
        with (
            patch("lilypad.traces.get_settings") as mock_settings,
            patch("lilypad.traces.get_sync_client") as mock_client,
        ):
            result = trace.tag()

            # Verify no API calls were made
            mock_settings.assert_not_called()
            mock_client.assert_not_called()
            assert result is None

    def test_annotate_with_no_annotations(self):
        """Test annotation with no annotation objects raises ValueError"""
        trace = Trace(response="test", span_id=123456789, function_uuid="test-func-uuid")

        # Empty annotation list should now raise ValueError with the critical fixes
        with pytest.raises(ValueError) as exc_info:
            trace.annotate()

        assert "At least one annotation must be provided" in str(exc_info.value)
