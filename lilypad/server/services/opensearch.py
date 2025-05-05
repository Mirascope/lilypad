"""The `OpenSearchClass` class for opensearch."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from opensearchpy import OpenSearch, RequestsHttpConnection
from pydantic import BaseModel, Field

from lilypad.server.settings import get_settings

from ..schemas.spans import SpanPublic

logger = logging.getLogger(__name__)
OPENSEARCH_INDEX_PREFIX = "traces_"


class FilterType(str, Enum):
    """Enum for filter types."""

    TERM = "term"
    RANGE = "range"
    EXISTS = "exists"
    WILDCARD = "wildcard"
    NESTED = "nested"


class TermFilter(BaseModel):
    """Term filter model."""

    field: str
    value: Any


class RangeFilter(BaseModel):
    """Range filter model."""

    field: str
    gt: float | None = None
    gte: float | None = None
    lt: float | None = None
    lte: float | None = None


class ExistsFilter(BaseModel):
    """Exists filter model."""

    field: str


class WildcardFilter(BaseModel):
    """Wildcard filter model."""

    field: str
    value: str


class NestedFilter(BaseModel):
    """Nested filter model."""

    path: str
    filter: dict[str, Filter]


class Filter(BaseModel):
    """Filter model."""

    type: FilterType
    term: TermFilter | None = None
    range: RangeFilter | None = None
    exists: ExistsFilter | None = None
    wildcard: WildcardFilter | None = None
    nested: NestedFilter | None = None


class OpenSearchQuery(BaseModel):
    """OpenSearch query model."""

    filters: list[Filter] = Field(default_factory=list)
    sort_field: str = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"
    limit: int = 100
    offset: int = 0
    query_string: str | None = None


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
                use_ssl=settings.opensearch_use_ssl,
                verify_certs=False,  # TODO Set to True in production with proper certificates
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

    def build_filter_query(self, filter_obj: Filter, parent_path: str = "") -> dict:
        """Build a query part for a single filter.

        Args:
            filter_obj: The filter object to process
            parent_path: Optional parent path for nested fields

        Returns:
            A properly formatted query part for OpenSearch
        """
        # Prepare the field path prefix if there's a parent path
        prefix = f"{parent_path}." if parent_path else ""

        if filter_obj.type == FilterType.TERM and filter_obj.term:
            return {"term": {f"{prefix}{filter_obj.term.field}": filter_obj.term.value}}

        elif filter_obj.type == FilterType.RANGE and filter_obj.range:
            range_dict = {}
            if filter_obj.range.gt is not None:
                range_dict["gt"] = filter_obj.range.gt
            if filter_obj.range.gte is not None:
                range_dict["gte"] = filter_obj.range.gte
            if filter_obj.range.lt is not None:
                range_dict["lt"] = filter_obj.range.lt
            if filter_obj.range.lte is not None:
                range_dict["lte"] = filter_obj.range.lte

            if range_dict:  # Only add if there are range conditions
                return {"range": {f"{prefix}{filter_obj.range.field}": range_dict}}

        elif filter_obj.type == FilterType.EXISTS and filter_obj.exists:
            return {"exists": {"field": f"{prefix}{filter_obj.exists.field}"}}

        elif filter_obj.type == FilterType.WILDCARD and filter_obj.wildcard:
            return {
                "wildcard": {
                    f"{prefix}{filter_obj.wildcard.field}": filter_obj.wildcard.value
                }
            }

        elif filter_obj.type == FilterType.NESTED and filter_obj.nested:
            # Handle nested filter type
            nested_path = f"{prefix}{filter_obj.nested.path}"
            nested_query_parts = []

            # Process each nested filter
            for (
                _,
                nested_filter_obj,
            ) in filter_obj.nested.filter.items():
                nested_query_part = self.build_filter_query(
                    nested_filter_obj, nested_path
                )
                if nested_query_part:
                    nested_query_parts.append(nested_query_part)

            if nested_query_parts:
                return {
                    "nested": {
                        "path": nested_path,
                        "query": {"bool": {"must": nested_query_parts}},
                    }
                }

        # Return empty dict if the filter doesn't match any type or is incomplete
        return {}

    def search_traces(self, project_uuid: UUID, search_query: OpenSearchQuery) -> Any:
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
                        "fields": ["span_id^2", "name^2", "data.*"],
                        "type": "best_fields",
                        "lenient": True,  # Makes the query lenient with type mismatches
                    }
                }
            )

        # Process all filters using the unified function
        for filter_item in search_query.filters:
            filter_query = self.build_filter_query(filter_item)
            if filter_query:  # Only add non-empty filter queries
                query_parts.append(filter_query)

        # Create the final query
        query = {"bool": {"must": query_parts}} if query_parts else {"match_all": {}}

        # Add sorting
        sort_config = [{search_query.sort_field: {"order": search_query.sort_order}}]

        # Execute the search
        search_body = {
            "query": query,
            "size": search_query.limit,
            "from": search_query.offset,
            "sort": sort_config,
            "track_scores": True,
        }

        try:
            logger.info(f"Query used: {search_body}")
            response = self.client.search(body=search_body, index=index_name)
            hits = response["hits"]["hits"]
            return hits
        except Exception as e:
            logger.error(f"OpenSearch error: {str(e)}")
            return []

    def delete_trace_by_uuid(self, project_uuid: UUID, span_uuid: UUID) -> bool:
        """Delete a single trace by its UUID.

        Args:
            project_uuid: The UUID of the project.
            span_uuid: The UUID of the span to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        if not self.client:
            logger.warning("OpenSearch client not initialized")
            return False

        index_name = self.get_index_name(project_uuid)

        if not self.client.indices.exists(index=index_name):
            logger.info(f"Index {index_name} does not exist, nothing to delete")
            return True

        try:
            response = self.client.delete(
                index=index_name,
                id=str(span_uuid),
            )

            result = response.get("result")
            if result == "deleted":
                logger.info(f"Successfully deleted trace with UUID {span_uuid}")
                return True
            elif result == "not_found":
                logger.info(f"Trace with UUID {span_uuid} not found, nothing to delete")
                return True
            else:
                logger.warning(
                    f"Unexpected result when deleting trace {span_uuid}: {result}"
                )
                return False
        except Exception as e:
            logger.error(f"Error deleting trace with UUID {span_uuid}: {str(e)}")
            return False

    def delete_traces_by_function_uuid(
        self, project_uuid: UUID, function_uuid: UUID
    ) -> bool:
        """Delete all traces associated with a specific function UUID.

        Args:
            project_uuid: The UUID of the project.
            function_uuid: The UUID of the function whose traces should be deleted.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        if not self.client:
            logger.warning("OpenSearch client not initialized")
            return False

        index_name = self.get_index_name(project_uuid)
        if not self.client.indices.exists(index=index_name):
            logger.info(f"Index {index_name} does not exist, nothing to delete")
            return True

        try:
            # First, find all span_ids with this function_uuid
            search_query = {
                "query": {"term": {"function_uuid": str(function_uuid)}},
                "_source": ["span_id"],
                "size": 10000,  # Adjust based on expected number of spans
            }

            search_response = self.client.search(index=index_name, body=search_query)

            # Extract all span_ids from the result
            span_ids = [
                hit["_source"]["span_id"]
                for hit in search_response.get("hits", {}).get("hits", [])
            ]

            if not span_ids:
                logger.info(f"No traces found for function {function_uuid}")
                return True

            # Delete all spans that have function_uuid or have parent_span_id in the list of span_ids
            delete_query = {
                "query": {
                    "bool": {
                        "should": [
                            {"term": {"function_uuid": str(function_uuid)}},
                            {"terms": {"parent_span_id": span_ids}},
                        ]
                    }
                }
            }

            response = self.client.delete_by_query(
                index=index_name,
                body=delete_query,
            )

            deleted_count = response.get("deleted", 0)
            logger.info(
                f"Successfully deleted {deleted_count} traces and child traces for function {function_uuid}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Error deleting traces and child traces for function {function_uuid}: {str(e)}"
            )
            return False


def get_opensearch_service() -> OpenSearchService:
    """Get the OpenSearch service instance."""
    return OpenSearchService()
