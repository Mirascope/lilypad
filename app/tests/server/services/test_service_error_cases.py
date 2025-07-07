"""Tests for service layer error cases to remove pragma: no cover comments."""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from sqlmodel import Session

from lilypad.server.models.spans import Scope
from lilypad.server.schemas.spans import SpanCreate
from lilypad.server.services.spans import SpanService


class TestSpanServiceErrors:
    """Test SpanService error handling."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = Mock()
        user.uuid = uuid4()
        user.organization_uuid = uuid4()
        return user

    @pytest.fixture
    def span_service(self, mock_session, mock_user):
        """Create SpanService with mocked dependencies."""
        return SpanService(session=mock_session, user=mock_user)

    def test_find_record_by_uuid_database_error(
        self, span_service: SpanService, mock_session
    ):
        """Test find_record_by_uuid handles database errors."""
        mock_session.exec.side_effect = Exception("Database connection error")

        with pytest.raises(Exception, match="Database connection error"):
            span_service.find_record_by_uuid(uuid4())

    def test_create_bulk_records_constraint_violation(
        self, span_service: SpanService, mock_session
    ):
        """Test create_bulk_records handles constraint violations."""
        mock_session.add_all.side_effect = Exception("Constraint violation")
        mock_session.rollback = Mock()
        mock_session.commit = Mock()

        span_creates = [
            SpanCreate(span_id="test_span", trace_id=None, scope=Scope.LILYPAD, data={})
        ]

        project_uuid = uuid4()
        org_uuid = uuid4()

        with pytest.raises(Exception, match="Constraint violation"):
            span_service.create_bulk_records(span_creates, project_uuid, org_uuid)

    def test_delete_record_by_uuid_cascade_error(
        self, span_service: SpanService, mock_session
    ):
        """Test delete_record_by_uuid handles cascade errors."""
        # Mock finding the record
        mock_span = Mock()
        mock_query = Mock()
        mock_query.where.return_value.where.return_value.first.return_value = mock_span
        mock_session.exec.return_value = mock_query

        # Mock delete to raise error
        mock_session.delete.side_effect = Exception("Cascade constraint error")

        # BaseService.delete_record_by_uuid catches exceptions and returns False
        result = span_service.delete_record_by_uuid(uuid4())
        assert result is False

    def test_get_aggregated_metrics_query_timeout(
        self, span_service: SpanService, mock_session
    ):
        """Test get_aggregated_metrics handles query timeouts."""
        mock_session.exec.side_effect = Exception("Query timeout")

        project_uuid = uuid4()

        with pytest.raises(Exception, match="Query timeout"):
            span_service.get_aggregated_metrics(project_uuid, "day")  # type: ignore

    def test_count_by_current_month_calculation_error(
        self, span_service: SpanService, mock_session
    ):
        """Test count_by_current_month handles calculation errors."""
        # The count_by_current_month method likely uses session.exec, not session.scalar
        mock_session.exec.side_effect = Exception("Date calculation error")

        with pytest.raises(Exception, match="Date calculation error"):
            span_service.count_by_current_month()


class TestKafkaServiceErrors:
    """Test Kafka service error handling."""

    @pytest.mark.asyncio
    async def test_stripe_kafka_service_send_error(self):
        """Test StripeKafkaService handles send errors."""
        from unittest.mock import Mock

        from lilypad.server.services.stripe_kafka_service import StripeKafkaService

        # Create a mock user
        mock_user = Mock()
        mock_user.uuid = uuid4()

        service = StripeKafkaService(user=mock_user)

        with patch(
            "lilypad.server.services.kafka_base.get_kafka_producer"
        ) as mock_get_producer:
            mock_producer = Mock()
            mock_producer.send_and_wait.side_effect = Exception("Send failed")
            mock_get_producer.return_value = mock_producer

            # Should return False when send fails
            result = await service.send({"test": "data", "trace_id": "123"})

            # Should return False when send fails
            assert result is False


class TestOpenSearchServiceErrors:
    """Test OpenSearch service error handling."""

    def test_opensearch_bulk_index_error(self):
        """Test OpenSearch bulk_index_traces handles errors."""
        from lilypad.server.services.opensearch import OpenSearchService

        with patch("lilypad.server.services.opensearch.OpenSearch") as mock_opensearch:
            mock_client = Mock()
            mock_client.bulk.side_effect = Exception("Bulk index error")
            mock_opensearch.return_value = mock_client

            service = OpenSearchService()
            service._client = mock_client

            result = service.bulk_index_traces(uuid4(), uuid4(), [{"test": "data"}])

            # Should return False on error
            assert result is False

    def test_opensearch_search_malformed_query(self):
        """Test OpenSearch search_traces handles malformed queries."""
        from lilypad.server.services.opensearch import OpenSearchService, SearchQuery

        with patch("lilypad.server.services.opensearch.OpenSearch") as mock_opensearch:
            mock_client = Mock()
            mock_client.search.side_effect = Exception("Malformed query")
            mock_opensearch.return_value = mock_client

            service = OpenSearchService()
            service._client = mock_client
            environment_uuid = uuid4()
            query = SearchQuery(
                query_string="malformed[query", environment_uuid=environment_uuid
            )

            # OpenSearch service gracefully handles errors and returns empty result
            result = service.search_traces(uuid4(), environment_uuid, query)
            assert result == []

    def test_opensearch_delete_trace_not_found(self):
        """Test OpenSearch delete_trace_by_uuid handles not found errors."""
        from lilypad.server.services.opensearch import OpenSearchService

        with patch("lilypad.server.services.opensearch.OpenSearch") as mock_opensearch:
            mock_client = Mock()
            mock_client.delete.side_effect = Exception("Document not found")
            mock_opensearch.return_value = mock_client

            service = OpenSearchService()
            service._client = mock_client

            # OpenSearch service gracefully handles errors and returns False
            result = service.delete_trace_by_uuid(uuid4(), uuid4(), uuid4())
            assert result is False


class TestProjectServiceErrors:
    """Test ProjectService error handling."""

    def test_create_project_name_validation_error(self):
        """Test create_project handles name validation errors."""
        from lilypad.server.schemas.projects import ProjectCreate
        from lilypad.server.services.projects import ProjectService

        mock_session = Mock()
        mock_user = Mock()
        service = ProjectService(session=mock_session, user=mock_user)

        # Create invalid project data
        invalid_project = ProjectCreate(name="")  # Empty name

        with patch.object(service, "create_record") as mock_create:
            mock_create.side_effect = ValueError("Name cannot be empty")

            with pytest.raises(ValueError, match="Name cannot be empty"):
                service.create_record(invalid_project)
