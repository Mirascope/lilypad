"""Simple tests for EE annotations API functions to improve coverage."""

import uuid
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest

# Import the functions to test  
from lilypad.ee.server.api.v0.annotations_api import (
    AnnotationMetrics,
    create_annotations,
    delete_annotation,
    get_annotation_metrics_by_function,
    get_annotations_by_functions,
    get_annotations_by_project,
    get_annotations_by_spans,
    update_annotation,
)


class TestAnnotationMetrics:
    """Test AnnotationMetrics model."""

    def test_annotation_metrics_creation(self):
        """Test creating AnnotationMetrics model."""
        function_uuid = uuid4()
        metrics = AnnotationMetrics(
            function_uuid=function_uuid,
            total_count=10,
            success_count=7,
        )
        
        assert metrics.function_uuid == function_uuid
        assert metrics.total_count == 10
        assert metrics.success_count == 7

    def test_annotation_metrics_serialization(self):
        """Test AnnotationMetrics serialization."""
        function_uuid = uuid4()
        metrics = AnnotationMetrics(
            function_uuid=function_uuid,
            total_count=15,
            success_count=12,
        )
        
        data = metrics.model_dump()
        assert data["function_uuid"] == function_uuid  # UUID serializes as UUID object, not string
        assert data["total_count"] == 15
        assert data["success_count"] == 12


class TestCreateAnnotations:
    """Test create_annotations function."""

    @pytest.mark.asyncio
    async def test_create_annotations_simple(self):
        """Test creating simple annotations."""
        # Mock services
        mock_annotation_service = Mock()
        mock_annotation_service.check_bulk_duplicates.return_value = []
        
        mock_annotation = Mock()
        mock_annotation.span = Mock()
        mock_annotation_service.create_bulk_records.return_value = [mock_annotation]
        
        mock_project_service = Mock()
        
        # Mock annotations create input
        annotations_create = [
            Mock(
                span_uuid=uuid4(),
                assignee_email=None,
                assigned_to=None,
                model_copy=Mock(return_value=Mock())
            )
        ]
        annotations_create[0].model_copy.return_value = annotations_create[0]
        
        project_uuid = uuid4()
        
        # Mock SpanMoreDetails.from_span
        with patch("lilypad.ee.server.api.v0.annotations_api.SpanMoreDetails") as mock_span_details:
            mock_span_details.from_span.return_value = {"test": "data"}
            
            with patch("lilypad.ee.server.api.v0.annotations_api.AnnotationPublic") as mock_public:
                mock_public.model_validate.return_value = {"result": "annotation"}
                
                result = await create_annotations(
                    project_uuid,
                    mock_annotation_service,
                    mock_project_service,
                    annotations_create,
                )
                
                assert result is not None
                mock_annotation_service.check_bulk_duplicates.assert_called_once()
                mock_annotation_service.create_bulk_records.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_annotations_with_email_lookup(self):
        """Test creating annotations with email lookup."""
        # Mock services
        mock_annotation_service = Mock()
        mock_annotation_service.check_bulk_duplicates.return_value = []
        
        mock_annotation = Mock()
        mock_annotation.span = Mock()
        mock_annotation_service.create_bulk_records.return_value = [mock_annotation]
        
        # Mock project with user organizations
        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.uuid = uuid4()
        
        mock_user_org = Mock()
        mock_user_org.user = mock_user
        
        mock_organization = Mock()
        mock_organization.user_organizations = [mock_user_org]
        
        mock_project = Mock()
        mock_project.organization = mock_organization
        
        mock_project_service = Mock()
        mock_project_service.find_record_by_uuid.return_value = mock_project
        
        # Mock annotations create input with assignee email
        mock_annotation_create = Mock()
        mock_annotation_create.span_uuid = uuid4()
        mock_annotation_create.assignee_email = ["test@example.com"]
        mock_annotation_create.assigned_to = None
        
        mock_copy = Mock()
        mock_copy.span_uuid = mock_annotation_create.span_uuid
        mock_copy.assigned_to = None
        mock_annotation_create.model_copy.return_value = mock_copy
        
        annotations_create = [mock_annotation_create]
        
        project_uuid = uuid4()
        
        # Mock SpanMoreDetails.from_span
        with patch("lilypad.ee.server.api.v0.annotations_api.SpanMoreDetails") as mock_span_details:
            mock_span_details.from_span.return_value = {"test": "data"}
            
            with patch("lilypad.ee.server.api.v0.annotations_api.AnnotationPublic") as mock_public:
                mock_public.model_validate.return_value = {"result": "annotation"}
                
                result = await create_annotations(
                    project_uuid,
                    mock_annotation_service,
                    mock_project_service,
                    annotations_create,
                )
                
                assert result is not None

    @pytest.mark.asyncio
    async def test_create_annotations_with_duplicates(self):
        """Test creating annotations with duplicates."""
        # Mock services
        mock_annotation_service = Mock()
        mock_annotation_service.check_bulk_duplicates.return_value = [uuid4()]  # Return duplicates
        
        mock_project_service = Mock()
        
        # Mock annotations create input
        annotations_create = [
            Mock(
                span_uuid=uuid4(),
                assignee_email=None,
                assigned_to=None,
                model_copy=Mock(return_value=Mock())
            )
        ]
        
        project_uuid = uuid4()
        
        # Should raise HTTPException
        with pytest.raises(Exception):  # HTTPException
            await create_annotations(
                project_uuid,
                mock_annotation_service,
                mock_project_service,
                annotations_create,
            )

    @pytest.mark.asyncio
    async def test_create_annotations_with_invalid_email(self):
        """Test creating annotations with invalid email."""
        # Mock services
        mock_annotation_service = Mock()
        
        # Mock project with no matching user
        mock_organization = Mock()
        mock_organization.user_organizations = []
        
        mock_project = Mock()
        mock_project.organization = mock_organization
        
        mock_project_service = Mock()
        mock_project_service.find_record_by_uuid.return_value = mock_project
        
        # Mock annotations create input with invalid email
        mock_annotation_create = Mock()
        mock_annotation_create.span_uuid = uuid4()
        mock_annotation_create.assignee_email = ["invalid@example.com"]
        mock_annotation_create.assigned_to = None
        
        mock_copy = Mock()
        mock_annotation_create.model_copy.return_value = mock_copy
        
        annotations_create = [mock_annotation_create]
        
        project_uuid = uuid4()
        
        # Should raise HTTPException
        with pytest.raises(Exception):  # HTTPException
            await create_annotations(
                project_uuid,
                mock_annotation_service,
                mock_project_service,
                annotations_create,
            )


class TestUpdateAnnotation:
    """Test update_annotation function."""

    @pytest.mark.asyncio
    async def test_update_annotation(self):
        """Test updating an annotation."""
        # Mock service
        mock_annotation = Mock()
        mock_annotation.span = Mock()
        
        mock_annotation_service = Mock()
        mock_annotation_service.update_record_by_uuid.return_value = mock_annotation
        
        # Mock annotation update
        mock_update = Mock()
        mock_update.model_dump.return_value = {"data": "updated"}
        
        annotation_uuid = uuid4()
        
        # Mock SpanMoreDetails.from_span and AnnotationPublic
        with patch("lilypad.ee.server.api.v0.annotations_api.SpanMoreDetails") as mock_span_details:
            mock_span_details.from_span.return_value = {"test": "data"}
            
            with patch("lilypad.ee.server.api.v0.annotations_api.AnnotationPublic") as mock_public:
                mock_public.model_validate.return_value = {"result": "updated"}
                
                result = await update_annotation(
                    annotation_uuid,
                    mock_annotation_service,
                    mock_update,
                )
                
                assert result is not None
                mock_annotation_service.update_record_by_uuid.assert_called_once()


class TestDeleteAnnotation:
    """Test delete_annotation function."""

    @pytest.mark.asyncio
    async def test_delete_annotation_success(self):
        """Test successful annotation deletion."""
        mock_annotation_service = Mock()
        mock_annotation_service.delete_record_by_uuid.return_value = True
        
        annotation_uuid = uuid4()
        
        result = await delete_annotation(annotation_uuid, mock_annotation_service)
        
        assert result is True
        mock_annotation_service.delete_record_by_uuid.assert_called_once_with(annotation_uuid)

    @pytest.mark.asyncio
    async def test_delete_annotation_not_found(self):
        """Test annotation deletion when not found."""
        mock_annotation_service = Mock()
        mock_annotation_service.delete_record_by_uuid.return_value = False
        
        annotation_uuid = uuid4()
        
        result = await delete_annotation(annotation_uuid, mock_annotation_service)
        
        assert result is False


class TestGetAnnotations:
    """Test get annotations functions."""

    @pytest.mark.asyncio
    async def test_get_annotations_by_functions(self):
        """Test getting annotations by function UUID."""
        # Mock service
        mock_annotation = Mock()
        mock_annotation.span = Mock()
        
        mock_annotation_service = Mock()
        mock_annotation_service.find_records_by_function_uuid.return_value = [mock_annotation]
        
        project_uuid = uuid4()
        function_uuid = uuid4()
        
        # Mock SpanMoreDetails.from_span and AnnotationPublic
        with patch("lilypad.ee.server.api.v0.annotations_api.SpanMoreDetails") as mock_span_details:
            mock_span_details.from_span.return_value = {"test": "data"}
            
            with patch("lilypad.ee.server.api.v0.annotations_api.AnnotationPublic") as mock_public:
                mock_public.model_validate.return_value = {"result": "annotation"}
                
                result = await get_annotations_by_functions(
                    project_uuid,
                    function_uuid,
                    mock_annotation_service,
                )
                
                assert result is not None
                mock_annotation_service.find_records_by_function_uuid.assert_called_once_with(function_uuid)

    @pytest.mark.asyncio
    async def test_get_annotations_by_spans(self):
        """Test getting annotations by span UUID."""
        # Mock service
        mock_annotation = Mock()
        mock_annotation.span = Mock()
        
        mock_annotation_service = Mock()
        mock_annotation_service.find_records_by_span_uuid.return_value = [mock_annotation]
        
        project_uuid = uuid4()
        span_uuid = uuid4()
        
        # Mock SpanMoreDetails.from_span and AnnotationPublic
        with patch("lilypad.ee.server.api.v0.annotations_api.SpanMoreDetails") as mock_span_details:
            mock_span_details.from_span.return_value = {"test": "data"}
            
            with patch("lilypad.ee.server.api.v0.annotations_api.AnnotationPublic") as mock_public:
                mock_public.model_validate.return_value = {"result": "annotation"}
                
                result = await get_annotations_by_spans(
                    project_uuid,
                    span_uuid,
                    mock_annotation_service,
                )
                
                assert result is not None
                mock_annotation_service.find_records_by_span_uuid.assert_called_once_with(span_uuid)

    @pytest.mark.asyncio
    async def test_get_annotations_by_project(self):
        """Test getting annotations by project UUID."""
        # Mock service
        mock_annotation = Mock()
        mock_annotation.span = Mock()
        
        mock_annotation_service = Mock()
        mock_annotation_service.find_records_by_project_uuid.return_value = [mock_annotation]
        
        project_uuid = uuid4()
        
        # Mock SpanMoreDetails.from_span and AnnotationPublic
        with patch("lilypad.ee.server.api.v0.annotations_api.SpanMoreDetails") as mock_span_details:
            mock_span_details.from_span.return_value = {"test": "data"}
            
            with patch("lilypad.ee.server.api.v0.annotations_api.AnnotationPublic") as mock_public:
                mock_public.model_validate.return_value = {"result": "annotation"}
                
                result = await get_annotations_by_project(
                    project_uuid,
                    mock_annotation_service,
                )
                
                assert result is not None
                mock_annotation_service.find_records_by_project_uuid.assert_called_once_with(project_uuid)


class TestGetAnnotationMetrics:
    """Test get annotation metrics function."""

    @pytest.mark.asyncio
    async def test_get_annotation_metrics_by_function(self):
        """Test getting annotation metrics by function UUID."""
        # Mock service
        mock_annotation_service = Mock()
        mock_annotation_service.find_metrics_by_function_uuid.return_value = (8, 12)  # (success, total)
        
        function_uuid = uuid4()
        
        result = await get_annotation_metrics_by_function(
            function_uuid,
            mock_annotation_service,
        )
        
        assert isinstance(result, AnnotationMetrics)
        assert result.function_uuid == function_uuid
        assert result.success_count == 8
        assert result.total_count == 12
        mock_annotation_service.find_metrics_by_function_uuid.assert_called_once_with(function_uuid)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_create_annotations_with_assigned_to(self):
        """Test creating annotations with assigned_to UUIDs."""
        # Mock services
        mock_annotation_service = Mock()
        mock_annotation_service.check_bulk_duplicates.return_value = []
        
        mock_annotation = Mock()
        mock_annotation.span = Mock()
        mock_annotation_service.create_bulk_records.return_value = [mock_annotation]
        
        mock_project_service = Mock()
        
        # Mock annotations create input with assigned_to
        user_uuid = uuid4()
        mock_annotation_create = Mock()
        mock_annotation_create.span_uuid = uuid4()
        mock_annotation_create.assignee_email = None
        mock_annotation_create.assigned_to = [user_uuid]
        mock_annotation_create.model_copy.return_value = mock_annotation_create
        
        annotations_create = [mock_annotation_create]
        
        project_uuid = uuid4()
        
        # Mock SpanMoreDetails.from_span
        with patch("lilypad.ee.server.api.v0.annotations_api.SpanMoreDetails") as mock_span_details:
            mock_span_details.from_span.return_value = {"test": "data"}
            
            with patch("lilypad.ee.server.api.v0.annotations_api.AnnotationPublic") as mock_public:
                mock_public.model_validate.return_value = {"result": "annotation"}
                
                result = await create_annotations(
                    project_uuid,
                    mock_annotation_service,
                    mock_project_service,
                    annotations_create,
                )
                
                assert result is not None

    @pytest.mark.asyncio
    async def test_create_annotations_no_assignee_or_assigned_to(self):
        """Test creating annotations without assignee or assigned_to."""
        # Mock services
        mock_annotation_service = Mock()
        mock_annotation_service.check_bulk_duplicates.return_value = []
        
        mock_annotation = Mock()
        mock_annotation.span = Mock()
        mock_annotation_service.create_bulk_records.return_value = [mock_annotation]
        
        mock_project_service = Mock()
        
        # Mock annotations create input without assignee or assigned_to
        mock_annotation_create = Mock()
        mock_annotation_create.span_uuid = uuid4()
        mock_annotation_create.assignee_email = None
        mock_annotation_create.assigned_to = None
        mock_annotation_create.model_copy.return_value = mock_annotation_create
        
        annotations_create = [mock_annotation_create]
        
        project_uuid = uuid4()
        
        # Mock SpanMoreDetails.from_span
        with patch("lilypad.ee.server.api.v0.annotations_api.SpanMoreDetails") as mock_span_details:
            mock_span_details.from_span.return_value = {"test": "data"}
            
            with patch("lilypad.ee.server.api.v0.annotations_api.AnnotationPublic") as mock_public:
                mock_public.model_validate.return_value = {"result": "annotation"}
                
                result = await create_annotations(
                    project_uuid,
                    mock_annotation_service,
                    mock_project_service,
                    annotations_create,
                )
                
                assert result is not None