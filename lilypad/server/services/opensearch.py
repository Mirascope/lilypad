"""The `OpenSearchClass` class for opensearch."""

import logging
from uuid import UUID

from opensearchpy import OpenSearch, RequestsHttpConnection
from pydantic import BaseModel

from lilypad.server.settings import get_settings

from ..models.spans import Scope
from ..schemas.spans import SpanPublic

logger = logging.getLogger(__name__)
OPENSEARCH_INDEX_PREFIX = "traces_"


class SearchQuery(BaseModel):
    """Search query parameters."""

    query_string: str
    time_range_start: int | None = None
    time_range_end: int | None = None
    limit: int = 100
    scope: Scope | None = None
    type: str | None = None


class SearchResult(BaseModel):
    """Search result model."""

    traces: list[SpanPublic]
    total_hits: int


# OpenSearch client service
class OpenSearchService:
    """Service for interacting with OpenSearch."""

    def __init__(self) -> None:
        """Initialize the OpenSearch client."""
        settings = get_settings()
        self.client = None
        if settings.opensearch_host and settings.opensearch_port:
            self.client = OpenSearch(
                hosts=[
                    {"host": settings.opensearch_host, "port": settings.opensearch_port}
                ],
                http_auth=(settings.opensearch_user, settings.opensearch_password)
                if settings.opensearch_user and settings.opensearch_password
                else None,
                use_ssl=False,
                verify_certs=False,  # For development. Set to True in production with proper certificates
                connection_class=RequestsHttpConnection,
                timeout=30,
            )
            self.is_enabled = True
        else:
            self.is_enabled = False

    def get_index_name(self, project_uuid: UUID) -> str:
        """Get the index name for a project."""
        return f"{OPENSEARCH_INDEX_PREFIX}{str(project_uuid)}"

    def ensure_index_exists(self, project_uuid: UUID) -> bool:
        """Create the index if it doesn't exist. Returns True if successful."""
        if not self.client:
            return False

        index_name = self.get_index_name(project_uuid)
        if not self.client.indices.exists(index=index_name):
            # Define the mapping for the trace documents
            mapping = {
                "mappings": {
                    "properties": {
                        "uuid": {"type": "keyword"},  # Add uuid field
                        "span_id": {"type": "keyword"},
                        "parent_span_id": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "function_uuid": {"type": "keyword"},
                        "scope": {"type": "keyword"},
                        "cost": {"type": "float"},
                        "input_tokens": {"type": "integer"},
                        "output_tokens": {"type": "integer"},
                        "duration_ms": {"type": "integer"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"},
                        "data": {"type": "object", "enabled": True},
                    }
                },
                "settings": {"number_of_shards": 1, "number_of_replicas": 1},
            }
            self.client.indices.create(index=index_name, body=mapping)
        return True

    def index_traces(self, project_uuid: UUID, trace: dict) -> bool:
        """Bulk index traces in OpenSearch. Returns True if successful.

        Args:
            project_uuid: The UUID of the project.
            trace: A dictionary created from model_dump().
        """
        if not self.client or not trace:
            return False

        if not self.ensure_index_exists(project_uuid):
            return False

        try:
            self.client.index(
                index=self.get_index_name(project_uuid),
                body=trace,
                id=str(trace.get("uuid")),
            )
            return True
        except Exception:
            return False

    def bulk_index_traces(self, project_uuid: UUID, traces: list[dict]) -> bool:
        """Bulk index traces in OpenSearch. Returns True if successful.

        Args:
            project_uuid: The UUID of the project.
            traces: A list of dictionaries created from model_dump().
        """
        if not self.client or not traces:
            return False

        if not self.ensure_index_exists(project_uuid):
            return False

        index_name = self.get_index_name(project_uuid)

        # Prepare bulk indexing actions
        actions = []
        for trace_dict in traces:
            # trace_dict is already a dictionary from model_dump(), so we can use it directly

            # Extract the UUID for the document ID (using "uuid" instead of "id")
            trace_id = str(trace_dict.get("uuid"))
            if not trace_id:
                continue

            # Add the index action
            actions.append({"index": {"_index": index_name, "_id": trace_id}})
            actions.append(trace_dict)

        if actions:
            # Execute the bulk operation
            try:
                self.client.bulk(body=actions)
                return True
            except Exception as e:
                logger.error(f"Error in bulk indexing: {str(e)}")
                return False
        return False

    def search_traces(
        self, project_uuid: UUID, search_query: SearchQuery
    ) -> SearchResult:
        """Search for traces in OpenSearch."""
        if not self.client:
            return SearchResult(traces=[], total_hits=0)
        index_name = self.get_index_name(project_uuid)

        # Check if index exists
        if not self.client.indices.exists(index=index_name):
            return SearchResult(traces=[], total_hits=0)

        # Build the query
        query_parts = []

        # Add query string if provided
        if search_query.query_string:
            query_parts.append(
                {
                    "multi_match": {
                        "query": search_query.query_string,
                        "fields": ["span_id", "type", "data.*"],
                        "type": "best_fields",
                    }
                }
            )

        # Add time range if provided
        if search_query.time_range_start or search_query.time_range_end:
            time_range = {}
            if search_query.time_range_start:
                time_range["gte"] = search_query.time_range_start
            if search_query.time_range_end:
                time_range["lte"] = search_query.time_range_end

            query_parts.append({"range": {"created_at": time_range}})

        # Add scope filter if provided
        if search_query.scope:
            query_parts.append({"term": {"scope": search_query.scope.value}})

        # Add type filter if provided
        if search_query.type:
            query_parts.append({"term": {"type": search_query.type}})

        query = {"bool": {"must": query_parts}} if query_parts else {"match_all": {}}

        # Execute the search
        search_body = {
            "query": query,
            "size": search_query.limit,
            "sort": [{"created_at": {"order": "desc"}}],
        }

        response = self.client.search(index=index_name, body=search_body)

        # Process results
        hits = response["hits"]["hits"]
        total_hits = response["hits"]["total"]["value"]

        # Convert OpenSearch results back to SpanPublic objects
        traces = []
        for hit in hits:
            source = hit["_source"]
            # Convert the OpenSearch document back to a SpanPublic object
            # You may need to adjust this based on your actual data structure
            trace = SpanPublic(
                uuid=hit["_id"],
                project_uuid=project_uuid,
                span_id=source["span_id"],
                parent_span_id=source["parent_span_id"],
                type=source["type"],
                function_uuid=UUID(source["function_uuid"])
                if source["function_uuid"]
                else None,
                scope=Scope(source["scope"]) if source["scope"] else None,
                cost=source["cost"],
                input_tokens=source["input_tokens"],
                output_tokens=source["output_tokens"],
                duration_ms=source["duration_ms"],
                created_at=source["created_at"],
                updated_at=source["updated_at"],  # type: ignore
                data=source["data"],
            )
            traces.append(trace)

        return SearchResult(traces=traces, total_hits=total_hits)


# Function to get OpenSearch service instance
def get_opensearch_service() -> OpenSearchService:
    """Get the OpenSearch service instance."""
    return OpenSearchService()
