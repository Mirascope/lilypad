"""Tests for the OpenSearch service."""

from unittest.mock import Mock, patch
from uuid import uuid4

from lilypad.server.models.spans import Scope
from lilypad.server.schemas.spans import SpanPublic
from lilypad.server.services.opensearch import (
    OPENSEARCH_INDEX_PREFIX,
    OpenSearchService,
    SearchQuery,
    SearchResult,
)


class TestSearchQuery:
    """Test SearchQuery model."""

    def test_search_query_defaults(self):
        """Test SearchQuery with default values."""
        query = SearchQuery()

        assert query.query_string is None
        assert query.time_range_start is None
        assert query.time_range_end is None
        assert query.limit == 100
        assert query.scope is None
        assert query.type is None

    def test_search_query_with_values(self):
        """Test SearchQuery with custom values."""
        query = SearchQuery(
            query_string="test query",
            time_range_start=1234567890,
            time_range_end=1234567999,
            limit=50,
            scope=Scope.LLM,
            type="generation",
        )

        assert query.query_string == "test query"
        assert query.time_range_start == 1234567890
        assert query.time_range_end == 1234567999
        assert query.limit == 50
        assert query.scope == Scope.LLM
        assert query.type == "generation"


class TestSearchResult:
    """Test SearchResult model."""

    def test_search_result_creation(self):
        """Test SearchResult creation."""
        mock_span = Mock(spec=SpanPublic)
        result = SearchResult(traces=[mock_span], total_hits=1)

        assert result.traces == [mock_span]
        assert result.total_hits == 1


class TestOpenSearchService:
    """Test OpenSearchService class."""

    @patch("lilypad.server.services.opensearch.get_settings")
    def test_init_with_settings(self, mock_get_settings):
        """Test OpenSearchService initialization with settings."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        service = OpenSearchService()

        assert service._host == "localhost"
        assert service._port == 9200
        assert service._user == "admin"
        assert service._password == "password"
        assert service._use_ssl is True
        assert service.is_enabled is True
        assert service._client is None

    @patch("lilypad.server.services.opensearch.get_settings")
    def test_init_disabled_no_host(self, mock_get_settings):
        """Test OpenSearchService initialization without host (disabled)."""
        mock_settings = Mock()
        mock_settings.opensearch_host = None
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        service = OpenSearchService()

        assert service._host is None
        assert service.is_enabled is False

    @patch("lilypad.server.services.opensearch.get_settings")
    def test_init_disabled_no_port(self, mock_get_settings):
        """Test OpenSearchService initialization without port (disabled)."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = None
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        service = OpenSearchService()

        assert service._port is None
        assert service.is_enabled is False

    @patch("lilypad.server.services.opensearch.get_settings")
    @patch("lilypad.server.services.opensearch.OpenSearch")
    def test_client_property_successful_connection(
        self, mock_opensearch_class, mock_get_settings
    ):
        """Test client property creates successful connection."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_client.indices = Mock()
        mock_client.indices.exists = Mock()
        mock_client.indices.create = Mock()
        mock_opensearch_class.return_value = mock_client

        service = OpenSearchService()

        with patch("lilypad.server.services.opensearch.logger") as mock_logger:
            client = service.client

        assert client == mock_client
        assert service._client == mock_client
        mock_opensearch_class.assert_called_once()
        mock_logger.info.assert_called_once_with("Successfully connected to OpenSearch")

    @patch("lilypad.server.services.opensearch.get_settings")
    @patch("lilypad.server.services.opensearch.OpenSearch")
    def test_client_property_connection_failure(
        self, mock_opensearch_class, mock_get_settings
    ):
        """Test client property handles connection failure."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        mock_opensearch_class.side_effect = Exception("Connection failed")

        service = OpenSearchService()

        with patch("lilypad.server.services.opensearch.logger") as mock_logger:
            client = service.client

        assert client is None
        assert service._client is None
        mock_logger.error.assert_called_once_with(
            "Failed to connect to OpenSearch: Connection failed"
        )

    @patch("lilypad.server.services.opensearch.get_settings")
    def test_client_property_disabled_service(self, mock_get_settings):
        """Test client property returns None when service is disabled."""
        mock_settings = Mock()
        mock_settings.opensearch_host = None
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        service = OpenSearchService()
        client = service.client

        assert client is None

    @patch("lilypad.server.services.opensearch.get_settings")
    @patch("lilypad.server.services.opensearch.OpenSearch")
    def test_client_property_no_auth(self, mock_opensearch_class, mock_get_settings):
        """Test client property creates connection without authentication."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = None
        mock_settings.opensearch_password = None
        mock_settings.opensearch_use_ssl = False
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_client.indices = Mock()
        mock_client.indices.exists = Mock()
        mock_client.indices.create = Mock()
        mock_opensearch_class.return_value = mock_client

        OpenSearchService()

        # Verify OpenSearch was called with correct parameters
        call_args = mock_opensearch_class.call_args
        assert call_args[1]["http_auth"] is None

    @patch("lilypad.server.services.opensearch.get_settings")
    def test_get_index_name(self, mock_get_settings):
        """Test get_index_name method."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = None
        mock_settings.opensearch_password = None
        mock_settings.opensearch_use_ssl = False
        mock_get_settings.return_value = mock_settings

        service = OpenSearchService()
        project_uuid = uuid4()

        index_name = service.get_index_name(project_uuid)

        assert index_name == f"{OPENSEARCH_INDEX_PREFIX}{str(project_uuid)}"

    @patch("lilypad.server.services.opensearch.get_settings")
    def test_ensure_index_exists_service_disabled(self, mock_get_settings):
        """Test ensure_index_exists when service is disabled."""
        mock_settings = Mock()
        mock_settings.opensearch_host = None
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = None
        mock_settings.opensearch_password = None
        mock_settings.opensearch_use_ssl = False
        mock_get_settings.return_value = mock_settings

        service = OpenSearchService()
        project_uuid = uuid4()

        result = service.ensure_index_exists(project_uuid)

        assert result is False

    @patch("lilypad.server.services.opensearch.get_settings")
    @patch("lilypad.server.services.opensearch.OpenSearch")
    def test_ensure_index_exists_index_already_exists(
        self, mock_opensearch_class, mock_get_settings
    ):
        """Test ensure_index_exists when index already exists."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_client.indices = Mock()
        mock_client.indices.exists = Mock()
        mock_client.indices.create = Mock()
        mock_client.indices.exists.return_value = True
        mock_opensearch_class.return_value = mock_client

        service = OpenSearchService()
        project_uuid = uuid4()

        result = service.ensure_index_exists(project_uuid)

        assert result is True
        mock_client.indices.exists.assert_called_once()
        mock_client.indices.create.assert_not_called()

    @patch("lilypad.server.services.opensearch.get_settings")
    @patch("lilypad.server.services.opensearch.OpenSearch")
    def test_ensure_index_exists_creates_new_index(
        self, mock_opensearch_class, mock_get_settings
    ):
        """Test ensure_index_exists creates new index."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_client.indices = Mock()
        mock_client.indices.exists = Mock()
        mock_client.indices.create = Mock()
        mock_client.indices.exists.return_value = False
        mock_client.indices.create.return_value = {"acknowledged": True}
        mock_opensearch_class.return_value = mock_client

        service = OpenSearchService()
        project_uuid = uuid4()

        with patch("lilypad.server.services.opensearch.logger") as mock_logger:
            result = service.ensure_index_exists(project_uuid)

        assert result is True
        mock_client.indices.exists.assert_called_once()
        mock_client.indices.create.assert_called_once()
        mock_logger.info.assert_called()

    @patch("lilypad.server.services.opensearch.get_settings")
    @patch("lilypad.server.services.opensearch.OpenSearch")
    def test_ensure_index_exists_creation_failure(
        self, mock_opensearch_class, mock_get_settings
    ):
        """Test ensure_index_exists handles creation failure."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_client.indices = Mock()
        mock_client.indices.exists = Mock()
        mock_client.indices.create = Mock()
        mock_client.indices.exists.return_value = False
        mock_client.indices.create.side_effect = Exception("Creation failed")
        mock_opensearch_class.return_value = mock_client

        service = OpenSearchService()
        project_uuid = uuid4()

        with patch("lilypad.server.services.opensearch.logger") as mock_logger:
            result = service.ensure_index_exists(project_uuid)

        assert result is False
        mock_logger.error.assert_called()

    @patch("lilypad.server.services.opensearch.get_settings")
    @patch("lilypad.server.services.opensearch.OpenSearch")
    def test_index_traces_success(self, mock_opensearch_class, mock_get_settings):
        """Test successful trace indexing."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_client.indices = Mock()
        mock_client.indices.exists = Mock()
        mock_client.indices.create = Mock()
        mock_client.index.return_value = {"_id": "test-id"}
        mock_opensearch_class.return_value = mock_client

        service = OpenSearchService()
        project_uuid = uuid4()
        trace_data = {"uuid": "test-uuid", "span_id": "test-span"}

        with patch.object(service, "ensure_index_exists", return_value=True):
            result = service.index_traces(project_uuid, trace_data)

        assert result is True
        mock_client.index.assert_called_once()

    @patch("lilypad.server.services.opensearch.get_settings")
    def test_index_traces_empty_trace(self, mock_get_settings):
        """Test index_traces with empty trace."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        service = OpenSearchService()
        project_uuid = uuid4()

        result = service.index_traces(project_uuid, {})
        assert result is False

    @patch("lilypad.server.services.opensearch.get_settings")
    def test_index_traces_no_client(self, mock_get_settings):
        """Test index_traces when client is not available."""
        mock_settings = Mock()
        mock_settings.opensearch_host = None
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        service = OpenSearchService()
        project_uuid = uuid4()
        trace_data = {"uuid": "test-uuid", "span_id": "test-span"}

        with patch("lilypad.server.services.opensearch.logger") as mock_logger:
            result = service.index_traces(project_uuid, trace_data)

        assert result is False
        mock_logger.warning.assert_called_with("OpenSearch client not available")

    @patch("lilypad.server.services.opensearch.get_settings")
    @patch("lilypad.server.services.opensearch.OpenSearch")
    def test_bulk_index_traces_success(self, mock_opensearch_class, mock_get_settings):
        """Test successful bulk trace indexing."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_client.indices = Mock()
        mock_client.indices.exists = Mock()
        mock_client.indices.create = Mock()
        mock_client.bulk.return_value = {"errors": False, "items": []}
        mock_opensearch_class.return_value = mock_client

        service = OpenSearchService()
        project_uuid = uuid4()
        traces = [
            {"uuid": "test-uuid-1", "span_id": "test-span-1"},
            {"uuid": "test-uuid-2", "span_id": "test-span-2"},
        ]

        with (
            patch.object(service, "ensure_index_exists", return_value=True),
            patch("lilypad.server.services.opensearch.logger") as mock_logger,
        ):
            result = service.bulk_index_traces(project_uuid, traces)

        assert result is True
        mock_client.bulk.assert_called_once()
        mock_logger.info.assert_called()

    @patch("lilypad.server.services.opensearch.get_settings")
    def test_bulk_index_traces_empty_list(self, mock_get_settings):
        """Test bulk_index_traces with empty list."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        service = OpenSearchService()
        project_uuid = uuid4()

        with patch("lilypad.server.services.opensearch.logger") as mock_logger:
            result = service.bulk_index_traces(project_uuid, [])

        assert result is False
        mock_logger.warning.assert_called_with("Empty traces list")

    @patch("lilypad.server.services.opensearch.get_settings")
    @patch("lilypad.server.services.opensearch.OpenSearch")
    def test_bulk_index_traces_with_errors(
        self, mock_opensearch_class, mock_get_settings
    ):
        """Test bulk_index_traces handles errors in response."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_client.indices = Mock()
        mock_client.indices.exists = Mock()
        mock_client.indices.create = Mock()
        mock_client.bulk.return_value = {
            "errors": True,
            "items": [{"index": {"error": "test error"}}],
        }
        mock_opensearch_class.return_value = mock_client

        service = OpenSearchService()
        project_uuid = uuid4()
        traces = [{"uuid": "test-uuid-1", "span_id": "test-span-1"}]

        with (
            patch.object(service, "ensure_index_exists", return_value=True),
            patch("lilypad.server.services.opensearch.logger") as mock_logger,
        ):
            result = service.bulk_index_traces(project_uuid, traces)

        assert result is False
        mock_logger.error.assert_called()

    @patch("lilypad.server.services.opensearch.get_settings")
    @patch("lilypad.server.services.opensearch.OpenSearch")
    def test_bulk_index_traces_no_actions_generated(
        self, mock_opensearch_class, mock_get_settings
    ):
        """Test bulk_index_traces when no valid actions are generated."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_client.indices = Mock()
        mock_client.indices.exists = Mock()
        mock_client.indices.create = Mock()
        mock_opensearch_class.return_value = mock_client

        service = OpenSearchService()
        project_uuid = uuid4()
        traces = []  # Empty traces list

        with patch.object(service, "ensure_index_exists", return_value=True):
            result = service.bulk_index_traces(project_uuid, traces)

        assert result is False

    @patch("lilypad.server.services.opensearch.get_settings")
    @patch("lilypad.server.services.opensearch.OpenSearch")
    def test_search_traces_no_index(self, mock_opensearch_class, mock_get_settings):
        """Test search_traces when index doesn't exist."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_client.indices = Mock()
        mock_client.indices.exists = Mock()
        mock_client.indices.create = Mock()
        mock_client.indices.exists.return_value = False
        mock_opensearch_class.return_value = mock_client

        service = OpenSearchService()
        project_uuid = uuid4()
        query = SearchQuery(query_string="test")

        result = service.search_traces(project_uuid, query)

        assert result == []

    @patch("lilypad.server.services.opensearch.get_settings")
    def test_search_traces_no_client(self, mock_get_settings):
        """Test search_traces when client is not available."""
        mock_settings = Mock()
        mock_settings.opensearch_host = None
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        service = OpenSearchService()
        project_uuid = uuid4()
        query = SearchQuery(query_string="test")

        with patch("lilypad.server.services.opensearch.logger") as mock_logger:
            result = service.search_traces(project_uuid, query)

        assert result == []
        mock_logger.warning.assert_called_with("OpenSearch client not available")

    @patch("lilypad.server.services.opensearch.get_settings")
    @patch("lilypad.server.services.opensearch.OpenSearch")
    def test_delete_trace_by_uuid_success(
        self, mock_opensearch_class, mock_get_settings
    ):
        """Test successful trace deletion by UUID."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_client.indices = Mock()
        mock_client.indices.exists = Mock()
        mock_client.indices.create = Mock()
        mock_client.indices.exists.return_value = True
        mock_client.delete.return_value = {"result": "deleted"}
        mock_opensearch_class.return_value = mock_client

        service = OpenSearchService()
        project_uuid = uuid4()
        span_uuid = uuid4()

        with patch("lilypad.server.services.opensearch.logger") as mock_logger:
            result = service.delete_trace_by_uuid(project_uuid, span_uuid)

        assert result is True
        mock_client.delete.assert_called_once()
        mock_logger.info.assert_called()

    @patch("lilypad.server.services.opensearch.get_settings")
    @patch("lilypad.server.services.opensearch.OpenSearch")
    def test_delete_trace_by_uuid_not_found(
        self, mock_opensearch_class, mock_get_settings
    ):
        """Test trace deletion when trace is not found."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_client.indices = Mock()
        mock_client.indices.exists = Mock()
        mock_client.indices.create = Mock()
        mock_client.indices.exists.return_value = True
        mock_client.delete.return_value = {"result": "not_found"}
        mock_opensearch_class.return_value = mock_client

        service = OpenSearchService()
        project_uuid = uuid4()
        span_uuid = uuid4()

        with patch("lilypad.server.services.opensearch.logger") as mock_logger:
            result = service.delete_trace_by_uuid(project_uuid, span_uuid)

        assert result is True
        mock_logger.info.assert_called()

    @patch("lilypad.server.services.opensearch.get_settings")
    @patch("lilypad.server.services.opensearch.OpenSearch")
    def test_delete_trace_by_uuid_no_index(
        self, mock_opensearch_class, mock_get_settings
    ):
        """Test delete_trace_by_uuid when index doesn't exist."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_client.indices = Mock()
        mock_client.indices.exists = Mock()
        mock_client.indices.create = Mock()
        mock_client.indices.exists.return_value = False
        mock_opensearch_class.return_value = mock_client

        service = OpenSearchService()
        project_uuid = uuid4()
        span_uuid = uuid4()

        with patch("lilypad.server.services.opensearch.logger") as mock_logger:
            result = service.delete_trace_by_uuid(project_uuid, span_uuid)

        assert result is True
        mock_logger.info.assert_called()

    @patch("lilypad.server.services.opensearch.get_settings")
    @patch("lilypad.server.services.opensearch.OpenSearch")
    def test_delete_traces_by_function_uuid_success(
        self, mock_opensearch_class, mock_get_settings
    ):
        """Test successful deletion of traces by function UUID."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_client.indices = Mock()
        mock_client.indices.exists = Mock()
        mock_client.indices.create = Mock()
        mock_client.indices.exists.return_value = True
        mock_client.search.return_value = {
            "hits": {
                "hits": [
                    {"_source": {"span_id": "span-1"}},
                    {"_source": {"span_id": "span-2"}},
                ]
            }
        }
        mock_client.delete_by_query.return_value = {"deleted": 2}
        mock_opensearch_class.return_value = mock_client

        service = OpenSearchService()
        project_uuid = uuid4()
        function_uuid = uuid4()

        with patch("lilypad.server.services.opensearch.logger") as mock_logger:
            result = service.delete_traces_by_function_uuid(project_uuid, function_uuid)

        assert result is True
        mock_client.search.assert_called_once()
        mock_client.delete_by_query.assert_called_once()
        mock_logger.info.assert_called()

    @patch("lilypad.server.services.opensearch.get_settings")
    @patch("lilypad.server.services.opensearch.OpenSearch")
    def test_delete_traces_by_function_uuid_no_traces(
        self, mock_opensearch_class, mock_get_settings
    ):
        """Test delete_traces_by_function_uuid when no traces found."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_client.indices = Mock()
        mock_client.indices.exists = Mock()
        mock_client.indices.create = Mock()
        mock_client.indices.exists.return_value = True
        mock_client.search.return_value = {"hits": {"hits": []}}
        mock_opensearch_class.return_value = mock_client

        service = OpenSearchService()
        project_uuid = uuid4()
        function_uuid = uuid4()

        with patch("lilypad.server.services.opensearch.logger") as mock_logger:
            result = service.delete_traces_by_function_uuid(project_uuid, function_uuid)

        assert result is True
        mock_logger.info.assert_called_with(
            f"No traces found for function {function_uuid}"
        )

    @patch("lilypad.server.services.opensearch.get_settings")
    def test_delete_traces_by_function_uuid_no_client(self, mock_get_settings):
        """Test delete_traces_by_function_uuid when client is not available."""
        mock_settings = Mock()
        mock_settings.opensearch_host = None
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        service = OpenSearchService()
        project_uuid = uuid4()
        function_uuid = uuid4()

        with patch("lilypad.server.services.opensearch.logger") as mock_logger:
            result = service.delete_traces_by_function_uuid(project_uuid, function_uuid)

        assert result is False
        mock_logger.warning.assert_called_with("OpenSearch client not available")


class TestGetOpenSearchService:
    """Test get_opensearch_service function."""

    @patch("lilypad.server.services.opensearch.get_settings")
    def test_get_opensearch_service(self, mock_get_settings):
        """Test get_opensearch_service returns service instance."""
        mock_settings = Mock()
        mock_settings.opensearch_host = "localhost"
        mock_settings.opensearch_port = 9200
        mock_settings.opensearch_user = "admin"
        mock_settings.opensearch_password = "password"
        mock_settings.opensearch_use_ssl = True
        mock_get_settings.return_value = mock_settings

        from lilypad.server.services.opensearch import get_opensearch_service

        service = get_opensearch_service()

        assert isinstance(service, OpenSearchService)
        assert service._host == "localhost"
