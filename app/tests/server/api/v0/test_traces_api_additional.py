"""Additional tests for traces API to improve coverage."""

from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi.testclient import TestClient


class TestConvertSystemToProvider:
    """Test _convert_system_to_provider function."""

    def test_convert_azure_system(self):
        """Test converting az.ai.inference to azure."""
        from lilypad.server.api.v0.traces_api import _convert_system_to_provider

        result = _convert_system_to_provider("az.ai.inference")
        assert result == "azure"

    def test_convert_google_system(self):
        """Test converting google_genai to google."""
        from lilypad.server.api.v0.traces_api import _convert_system_to_provider

        result = _convert_system_to_provider("google_genai")
        assert result == "google"

    def test_convert_other_system(self):
        """Test converting other systems (passthrough)."""
        from lilypad.server.api.v0.traces_api import _convert_system_to_provider

        result = _convert_system_to_provider("openai")
        assert result == "openai"


class TestGetTraceBySpanUuid:
    """Test get_trace_by_span_uuid endpoint."""

    @patch("lilypad.server.api.v0.traces_api.SpanService")
    def test_get_trace_by_span_uuid_not_found(
        self, mock_service_cls, client: TestClient
    ):
        """Test getting trace when span not found."""
        # Mock service to return None
        mock_service = Mock()
        mock_service.find_root_parent_span.return_value = None
        mock_service_cls.return_value = mock_service

        project_uuid = uuid4()
        span_id = "nonexistent_span"

        response = client.get(f"/projects/{project_uuid}/traces/{span_id}/root")
        assert response.status_code == 404
        assert "Span not found" in response.json()["detail"]

    @patch("lilypad.server.api.v0.traces_api.SpanService")
    def test_get_trace_by_span_uuid_success(self, mock_service_cls, client: TestClient):
        """Test getting trace successfully."""
        # Mock service to return a span
        mock_service = Mock()
        mock_span = Mock()
        mock_span.span_id = "test_span"
        mock_span.uuid = uuid4()
        mock_service.find_root_parent_span.return_value = mock_span
        mock_service_cls.return_value = mock_service

        project_uuid = uuid4()
        span_id = "test_span"

        response = client.get(f"/projects/{project_uuid}/traces/{span_id}/root")
        assert response.status_code == 200


class TestGetSpansByTraceId:
    """Test get_spans_by_trace_id endpoint."""

    @patch("lilypad.server.api.v0.traces_api.SpanService")
    def test_get_spans_by_trace_id_not_found(
        self, mock_service_cls, client: TestClient
    ):
        """Test getting spans when none found for trace ID."""
        # Mock service to return empty list
        mock_service = Mock()
        mock_service.find_spans_by_trace_id.return_value = []
        mock_service_cls.return_value = mock_service

        project_uuid = uuid4()
        trace_id = "nonexistent_trace"

        response = client.get(f"/projects/{project_uuid}/traces/by-trace-id/{trace_id}")
        assert response.status_code == 404
        assert f"No spans found for trace_id: {trace_id}" in response.json()["detail"]

    @patch("lilypad.server.api.v0.traces_api.SpanService")
    def test_get_spans_by_trace_id_success(self, mock_service_cls, client: TestClient):
        """Test getting spans successfully."""
        # Mock service to return spans
        mock_service = Mock()
        mock_span = Mock()
        mock_span.uuid = uuid4()
        mock_span.span_id = "test_span"
        mock_service.find_spans_by_trace_id.return_value = [mock_span]
        mock_service_cls.return_value = mock_service

        project_uuid = uuid4()
        trace_id = "test_trace"

        response = client.get(f"/projects/{project_uuid}/traces/by-trace-id/{trace_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


class TestIndexTracesInOpenSearch:
    """Test index_traces_in_opensearch function."""

    def test_index_traces_success(self):
        """Test successful trace indexing."""
        import asyncio

        from lilypad.server.api.v0.traces_api import index_traces_in_opensearch

        mock_opensearch = Mock()
        mock_opensearch.bulk_index_traces.return_value = True

        project_uuid = uuid4()
        traces = [{"span_id": "test_span", "data": "test"}]

        async def test_index():
            await index_traces_in_opensearch(project_uuid, traces, mock_opensearch)
            mock_opensearch.bulk_index_traces.assert_called_once_with(
                project_uuid, traces
            )

        asyncio.run(test_index())

    def test_index_traces_failure(self):
        """Test trace indexing failure."""
        import asyncio

        from lilypad.server.api.v0.traces_api import index_traces_in_opensearch

        mock_opensearch = Mock()
        mock_opensearch.bulk_index_traces.return_value = False  # Failure

        project_uuid = uuid4()
        traces = [{"span_id": "test_span", "data": "test"}]

        async def test_index():
            await index_traces_in_opensearch(project_uuid, traces, mock_opensearch)
            mock_opensearch.bulk_index_traces.assert_called_once_with(
                project_uuid, traces
            )

        asyncio.run(test_index())

    def test_index_traces_exception(self):
        """Test trace indexing with exception."""
        import asyncio

        from lilypad.server.api.v0.traces_api import index_traces_in_opensearch

        mock_opensearch = Mock()
        mock_opensearch.bulk_index_traces.side_effect = Exception("OpenSearch error")

        project_uuid = uuid4()
        traces = [{"span_id": "test_span", "data": "test"}]

        async def test_index():
            await index_traces_in_opensearch(project_uuid, traces, mock_opensearch)
            mock_opensearch.bulk_index_traces.assert_called_once_with(
                project_uuid, traces
            )

        asyncio.run(test_index())


class TestTracesEndpointAdditional:
    """Test additional scenarios for traces endpoint."""

    @patch("lilypad.server.api.v0.traces_api.get_span_kafka_service")
    @patch("lilypad.server.api.v0.traces_api.get_opensearch_service")
    @patch("lilypad.server.api.v0.traces_api.BillingService")
    @patch("lilypad.server.api.v0.traces_api.ProjectService")
    @patch("lilypad.server.api.v0.traces_api.SpanService")
    def test_traces_with_missing_attributes(
        self,
        mock_span_service_cls,
        mock_project_service_cls,
        mock_billing_service_cls,
        mock_get_opensearch,
        mock_get_kafka,
        client: TestClient,
    ):
        """Test traces processing with spans missing attributes."""
        # Mock services
        mock_span_service = Mock()
        mock_span_service.count_by_current_month.return_value = 0
        mock_span_service.create_bulk_records.return_value = []
        mock_span_service_cls.return_value = mock_span_service

        mock_project_service = Mock()
        mock_project = Mock()
        mock_project.organization_uuid = uuid4()
        mock_project_service.find_record_no_organization.return_value = mock_project
        mock_project_service_cls.return_value = mock_project_service

        mock_billing_service_cls.return_value = Mock()

        mock_opensearch = Mock()
        mock_opensearch.is_enabled = False
        mock_get_opensearch.return_value = mock_opensearch

        mock_kafka = Mock()
        mock_kafka.send_batch.return_value = False  # Force fallback processing
        mock_get_kafka.return_value = mock_kafka

        project_uuid = uuid4()

        # Trace data without attributes
        traces_data = [
            {
                "span_id": "test_span_1",
                "trace_id": "test_trace_1",
                "parent_span_id": None,
                "start_time": 1000,
                "end_time": 2000,
                "instrumentation_scope": {"name": "lilypad"},
                # Missing attributes - should be added
            }
        ]

        response = client.post(f"/projects/{project_uuid}/traces", json=traces_data)
        assert response.status_code == 200
        data = response.json()
        assert data["trace_status"] == "processed"

    @patch("lilypad.server.api.v0.traces_api.get_span_kafka_service")
    @patch("lilypad.server.api.v0.traces_api.get_opensearch_service")
    @patch("lilypad.server.api.v0.traces_api.BillingService")
    @patch("lilypad.server.api.v0.traces_api.ProjectService")
    @patch("lilypad.server.api.v0.traces_api.SpanService")
    def test_traces_with_parent_span_id_walrus_operator(
        self,
        mock_span_service_cls,
        mock_project_service_cls,
        mock_billing_service_cls,
        mock_get_opensearch,
        mock_get_kafka,
        client: TestClient,
    ):
        """Test traces processing to trigger walrus operator on line 288."""
        # Mock services
        mock_span_service = Mock()
        mock_span_service.count_by_current_month.return_value = 0
        mock_span_service.create_bulk_records.return_value = []
        mock_span_service_cls.return_value = mock_span_service

        mock_project_service = Mock()
        mock_project = Mock()
        mock_project.organization_uuid = uuid4()
        mock_project_service.find_record_no_organization.return_value = mock_project
        mock_project_service_cls.return_value = mock_project_service

        mock_billing_service_cls.return_value = Mock()

        mock_opensearch = Mock()
        mock_opensearch.is_enabled = False
        mock_get_opensearch.return_value = mock_opensearch

        mock_kafka = Mock()
        mock_kafka.send_batch.return_value = False  # Force fallback processing
        mock_get_kafka.return_value = mock_kafka

        project_uuid = uuid4()

        # Trace data with parent_span_id to trigger the walrus operator
        traces_data = [
            {
                "span_id": "parent_span",
                "trace_id": "test_trace_1",
                "parent_span_id": None,
                "start_time": 1000,
                "end_time": 2000,
                "instrumentation_scope": {"name": "lilypad"},
                "attributes": {},
            },
            {
                "span_id": "child_span",
                "trace_id": "test_trace_1",
                "parent_span_id": "parent_span",  # This triggers the walrus operator
                "start_time": 1500,
                "end_time": 1800,
                "instrumentation_scope": {"name": "lilypad"},
                "attributes": {},
            },
        ]

        response = client.post(f"/projects/{project_uuid}/traces", json=traces_data)
        assert response.status_code == 200
        data = response.json()
        assert data["trace_status"] == "processed"

    @patch("lilypad.server.api.v0.traces_api.get_span_kafka_service")
    @patch("lilypad.server.api.v0.traces_api.get_opensearch_service")
    @patch("lilypad.server.api.v0.traces_api.BillingService")
    @patch("lilypad.server.api.v0.traces_api.ProjectService")
    @patch("lilypad.server.api.v0.traces_api.SpanService")
    def test_traces_with_opensearch_enabled(
        self,
        mock_span_service_cls,
        mock_project_service_cls,
        mock_billing_service_cls,
        mock_get_opensearch,
        mock_get_kafka,
        client: TestClient,
    ):
        """Test traces processing with OpenSearch enabled."""
        # Mock services
        mock_span_service = Mock()
        mock_span_service.count_by_current_month.return_value = 0
        mock_span_tables = [Mock()]
        mock_span_tables[0].model_dump.return_value = {"span_id": "test_span"}
        mock_span_service.create_bulk_records.return_value = mock_span_tables
        mock_span_service_cls.return_value = mock_span_service

        mock_project_service = Mock()
        mock_project = Mock()
        mock_project.organization_uuid = uuid4()
        mock_project_service.find_record_no_organization.return_value = mock_project
        mock_project_service_cls.return_value = mock_project_service

        mock_billing_service_cls.return_value = Mock()

        mock_opensearch = Mock()
        mock_opensearch.is_enabled = True  # Enable OpenSearch
        mock_get_opensearch.return_value = mock_opensearch

        mock_kafka = Mock()
        mock_kafka.send_batch.return_value = False  # Force fallback processing
        mock_get_kafka.return_value = mock_kafka

        project_uuid = uuid4()

        # Simple trace data
        traces_data = [
            {
                "span_id": "test_span_1",
                "trace_id": "test_trace_1",
                "parent_span_id": None,
                "start_time": 1000,
                "end_time": 2000,
                "instrumentation_scope": {"name": "lilypad"},
                "attributes": {},
            }
        ]

        response = client.post(f"/projects/{project_uuid}/traces", json=traces_data)
        assert response.status_code == 200
        data = response.json()
        assert data["trace_status"] == "processed"


class TestProcessSpanEdgeCases:
    """Test edge cases in span processing that might be missed."""

    @patch("lilypad.server.api.v0.traces_api.get_span_kafka_service")
    @patch("lilypad.server.api.v0.traces_api.get_opensearch_service")
    @patch("lilypad.server.api.v0.traces_api.BillingService")
    @patch("lilypad.server.api.v0.traces_api.ProjectService")
    @patch("lilypad.server.api.v0.traces_api.SpanService")
    def test_traces_with_llm_span_az_inference(
        self,
        mock_span_service_cls,
        mock_project_service_cls,
        mock_billing_service_cls,
        mock_get_opensearch,
        mock_get_kafka,
        client: TestClient,
    ):
        """Test LLM span processing with az.ai.inference system."""
        # Mock services
        mock_span_service = Mock()
        mock_span_service.count_by_current_month.return_value = 0
        mock_span_service.create_bulk_records.return_value = []
        mock_span_service_cls.return_value = mock_span_service

        mock_project_service = Mock()
        mock_project = Mock()
        mock_project.organization_uuid = uuid4()
        mock_project_service.find_record_no_organization.return_value = mock_project
        mock_project_service_cls.return_value = mock_project_service

        mock_billing_service_cls.return_value = Mock()

        mock_opensearch = Mock()
        mock_opensearch.is_enabled = False
        mock_get_opensearch.return_value = mock_opensearch

        mock_kafka = Mock()
        mock_kafka.send_batch.return_value = False  # Force fallback processing
        mock_get_kafka.return_value = mock_kafka

        project_uuid = uuid4()

        # LLM span with az.ai.inference system to test line 52
        traces_data = [
            {
                "span_id": "llm_span",
                "trace_id": "test_trace_1",
                "parent_span_id": None,
                "start_time": 1000,
                "end_time": 2000,
                "instrumentation_scope": {
                    "name": "other"
                },  # Not lilypad to trigger LLM processing
                "attributes": {
                    "gen_ai.system": "az.ai.inference",  # This should trigger line 52
                    "gen_ai.response.model": "gpt-4",
                    "gen_ai.usage.input_tokens": 100,
                    "gen_ai.usage.output_tokens": 50,
                },
            }
        ]

        response = client.post(f"/projects/{project_uuid}/traces", json=traces_data)
        assert response.status_code == 200

    @patch("lilypad.server.api.v0.traces_api.get_span_kafka_service")
    @patch("lilypad.server.api.v0.traces_api.get_opensearch_service")
    @patch("lilypad.server.api.v0.traces_api.BillingService")
    @patch("lilypad.server.api.v0.traces_api.ProjectService")
    @patch("lilypad.server.api.v0.traces_api.SpanService")
    def test_traces_with_llm_span_google_genai(
        self,
        mock_span_service_cls,
        mock_project_service_cls,
        mock_billing_service_cls,
        mock_get_opensearch,
        mock_get_kafka,
        client: TestClient,
    ):
        """Test LLM span processing with google_genai system."""
        # Mock services
        mock_span_service = Mock()
        mock_span_service.count_by_current_month.return_value = 0
        mock_span_service.create_bulk_records.return_value = []
        mock_span_service_cls.return_value = mock_span_service

        mock_project_service = Mock()
        mock_project = Mock()
        mock_project.organization_uuid = uuid4()
        mock_project_service.find_record_no_organization.return_value = mock_project
        mock_project_service_cls.return_value = mock_project_service

        mock_billing_service_cls.return_value = Mock()

        mock_opensearch = Mock()
        mock_opensearch.is_enabled = False
        mock_get_opensearch.return_value = mock_opensearch

        mock_kafka = Mock()
        mock_kafka.send_batch.return_value = False  # Force fallback processing
        mock_get_kafka.return_value = mock_kafka

        project_uuid = uuid4()

        # LLM span with google_genai system to test line 54
        traces_data = [
            {
                "span_id": "llm_span",
                "trace_id": "test_trace_1",
                "parent_span_id": None,
                "start_time": 1000,
                "end_time": 2000,
                "instrumentation_scope": {
                    "name": "other"
                },  # Not lilypad to trigger LLM processing
                "attributes": {
                    "gen_ai.system": "google_genai",  # This should trigger line 54
                    "gen_ai.response.model": "gemini-pro",
                    "gen_ai.usage.input_tokens": 100,
                    "gen_ai.usage.output_tokens": 50,
                },
            }
        ]

        response = client.post(f"/projects/{project_uuid}/traces", json=traces_data)
        assert response.status_code == 200
