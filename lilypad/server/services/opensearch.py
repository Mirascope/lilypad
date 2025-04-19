"""The `OpenSearchClass` class for opensearch."""

import logging
from typing import Any
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
                        "duration_ms": {"type": "long"},
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
            logger.warning("OpenSearch client not initialized or empty traces list")
            return False

        if not self.ensure_index_exists(project_uuid):
            logger.error(f"Failed to ensure index exists for project {project_uuid}")
            return False

        index_name = self.get_index_name(project_uuid)

        # Prepare bulk indexing actions
        actions = []
        for trace_dict in traces:
            # Extract the UUID for the document ID
            trace_id = str(trace_dict.get("uuid"))
            if not trace_id:
                logger.warning("Skipping trace without UUID")
                continue

            # Add the index action
            actions.append({"index": {"_index": index_name, "_id": trace_id}})
            actions.append(trace_dict)

        if actions:
            try:
                response = self.client.bulk(body=actions)

                # Check for errors in the response
                if response.get("errors", False):
                    error_items = [
                        item
                        for item in response.get("items", [])
                        if "error" in item.get("index", {})
                    ]
                    logger.error(f"Bulk indexing had errors: {error_items[:5]}")
                    return False

                logger.info(f"Successfully indexed {len(actions) // 2} traces")
                return True
            except Exception as e:
                logger.error(f"Error in bulk indexing: {str(e)}")
                return False
        return False

    def search_traces(self, project_uuid: UUID, search_query: SearchQuery) -> Any:
        """Search for traces in OpenSearch."""
        if not self.client:
            return []
        index_name = self.get_index_name(project_uuid)

        # Check if index exists
        if not self.client.indices.exists(index=index_name):
            return []

        # Build the query
        query_parts = []

        # Add query string if provided
        if search_query.query_string:
            query_parts.append(
                {
                    "multi_match": {
                        "query": search_query.query_string,
                        "fields": ["span_id^2", "type^2", "name^2", "data.*"],
                        "type": "best_fields",
                        "lenient": True,  # Makes the query lenient with type mismatches
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

        # Create the final query
        query = {"bool": {"must": query_parts}} if query_parts else {"match_all": {}}

        # Execute the search
        search_body = {
            "query": query,
            "size": search_query.limit,
            "sort": [{"created_at": {"order": "desc"}}],
        }

        try:
            response = self.client.search(body=search_body, index=index_name)
            hits = response["hits"]["hits"]
            return hits
        except Exception as e:
            logger.error(f"OpenSearch error: {str(e)}")
            logger.info(f"Query used: {search_body}")
            return []


def get_opensearch_service() -> OpenSearchService:
    """Get the OpenSearch service instance."""
    return OpenSearchService()
