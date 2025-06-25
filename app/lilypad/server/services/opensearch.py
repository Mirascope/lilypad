"""The `OpenSearchClass` class for opensearch."""

import logging
from datetime import datetime
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

    query_string: str | None = None
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
        """Initialize the OpenSearch service with lazy connection."""
        settings = get_settings()
        self._client: OpenSearch | None = None
        self._host = settings.opensearch_host
        self._port = settings.opensearch_port
        self._user = settings.opensearch_user
        self._password = settings.opensearch_password
        self._use_ssl = settings.opensearch_use_ssl
        self.is_enabled = bool(self._host and self._port)

    @property
    def client(self) -> OpenSearch | None:
        """Get the OpenSearch client, initializing it if necessary."""
        if self._client is None and self.is_enabled:
            try:
                self._client = OpenSearch(
                    hosts=[{"host": self._host, "port": self._port}],
                    http_auth=(self._user, self._password)
                    if self._user and self._password
                    else None,
                    use_ssl=self._use_ssl,
                    verify_certs=False,  # TODO Set to True in production with proper certificates
                    connection_class=RequestsHttpConnection,
                    timeout=5,
                )
                logger.info("Successfully connected to OpenSearch")
            except Exception as e:
                logger.error(f"Failed to connect to OpenSearch: {str(e)}")
                self._client = None
        return self._client

    def get_index_name(self, project_uuid: UUID) -> str:
        """Get the index name for a project."""
        return f"{OPENSEARCH_INDEX_PREFIX}{str(project_uuid)}"

    def ensure_index_exists(self, project_uuid: UUID) -> bool:
        """Create the index if it doesn't exist. Returns True if successful."""
        if not self.client:
            return False

        index_name = self.get_index_name(project_uuid)
        try:
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
        except Exception as e:
            logger.error(f"Error ensuring index exists: {str(e)}")
            return False

    def index_traces(self, project_uuid: UUID, trace: dict) -> bool:
        """Index a single trace in OpenSearch. Returns True if successful."""
        if not trace:
            return False

        if not self.client:
            logger.warning("OpenSearch client not available")
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
        except Exception as e:
            logger.error(f"Error indexing trace: {str(e)}")
            return False

    def bulk_index_traces(self, project_uuid: UUID, traces: list[dict]) -> bool:
        """Bulk index traces in OpenSearch. Returns True if successful."""
        if not traces:
            logger.warning("Empty traces list")
            return False

        if not self.client:
            logger.warning("OpenSearch client not available")
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
            logger.warning("OpenSearch client not available")
            return []

        index_name = self.get_index_name(project_uuid)

        # Check if index exists
        try:
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
            query = (
                {"bool": {"must": query_parts}} if query_parts else {"match_all": {}}
            )

            # Execute the search
            search_body = {
                "query": query,
                "size": search_query.limit,
                "track_scores": True,
            }

            logger.info(f"Query used: {search_body}")
            response = self.client.search(body=search_body, index=index_name)
            hits = response["hits"]["hits"]
            return hits
        except Exception as e:
            logger.error(f"OpenSearch error: {str(e)}")
            return []

    def delete_trace_by_uuid(self, project_uuid: UUID, span_uuid: UUID) -> bool:
        """Delete a single trace by its UUID."""
        if not self.client:
            logger.warning("OpenSearch client not available")
            return False

        index_name = self.get_index_name(project_uuid)

        try:
            if not self.client.indices.exists(index=index_name):
                logger.info(f"Index {index_name} does not exist, nothing to delete")
                return True

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
        """Delete all traces associated with a specific function UUID."""
        if not self.client:
            logger.warning("OpenSearch client not available")
            return False

        index_name = self.get_index_name(project_uuid)

        try:
            if not self.client.indices.exists(index=index_name):
                logger.info(f"Index {index_name} does not exist, nothing to delete")
                return True

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

    def delete_traces_older_than(
        self, project_uuid: UUID, cutoff_date: datetime
    ) -> tuple[bool, int]:
        """Delete all traces older than a specific date for a project.

        Args:
            project_uuid: The project UUID to delete traces for
            cutoff_date: The cutoff date as datetime object

        Returns:
            Tuple of (success: bool, deleted_count: int)
        """
        if not self.client:
            logger.warning("OpenSearch client not available")
            return False, 0

        index_name = self.get_index_name(project_uuid)

        try:
            if not self.client.indices.exists(index=index_name):
                logger.info(f"Index {index_name} does not exist, nothing to delete")
                return True, 0

            # Convert datetime to ISO format for OpenSearch
            cutoff_date_str = cutoff_date.isoformat()

            # Build the range query for documents older than cutoff_date
            delete_query = {"query": {"range": {"created_at": {"lt": cutoff_date_str}}}}

            # Execute delete by query
            response = self.client.delete_by_query(index=index_name, body=delete_query)

            deleted_count = response.get("deleted", 0)
            failures = response.get("failures", [])

            if failures:
                logger.warning(
                    f"Some documents failed to delete from {index_name}: {failures[:5]}"
                )

            logger.info(
                f"Successfully deleted {deleted_count} traces older than {cutoff_date_str} "
                f"from project {project_uuid}"
            )
            return True, deleted_count
        except Exception as e:
            logger.error(
                f"Error deleting old traces for project {project_uuid}: {str(e)}"
            )
            return False, 0

    def delete_traces_by_uuids(
        self, project_uuid: UUID, span_uuids: list[UUID], batch_size: int = 1000
    ) -> tuple[bool, int]:
        """Delete specific traces by their UUIDs with batch processing.

        Args:
            project_uuid: The project UUID
            span_uuids: List of span UUIDs to delete
            batch_size: Number of UUIDs to process in each batch (default: 1000)

        Returns:
            Tuple of (success: bool, deleted_count: int)
        """
        if not self.client:
            logger.warning("OpenSearch client not available")
            return False, 0

        if not span_uuids:
            return True, 0

        index_name = self.get_index_name(project_uuid)

        try:
            if not self.client.indices.exists(index=index_name):
                logger.info(f"Index {index_name} does not exist, nothing to delete")
                return True, 0

            # Convert UUIDs to strings
            uuid_strings = [str(uuid) for uuid in span_uuids]

            total_deleted = 0
            total_failures = 0

            # Process in batches to avoid query size limits
            for i in range(0, len(uuid_strings), batch_size):
                batch_uuids = uuid_strings[i : i + batch_size]

                # Build the terms query for this batch
                delete_query = {"query": {"terms": {"uuid": batch_uuids}}}

                # Execute delete by query for this batch
                response = self.client.delete_by_query(
                    index=index_name, body=delete_query
                )

                batch_deleted = response.get("deleted", 0)
                batch_failures = response.get("failures", [])

                total_deleted += batch_deleted

                if batch_failures:
                    total_failures += len(batch_failures)
                    logger.warning(
                        f"Batch {i // batch_size + 1}: {len(batch_failures)} documents "
                        f"failed to delete from {index_name}"
                    )

                logger.debug(
                    f"Batch {i // batch_size + 1}: Deleted {batch_deleted} traces "
                    f"from project {project_uuid}"
                )

            if total_failures > 0:
                logger.warning(
                    f"Total failures during deletion: {total_failures} documents"
                )

            logger.info(
                f"Successfully deleted {total_deleted} traces by UUID from project {project_uuid} "
                f"in {len(range(0, len(uuid_strings), batch_size))} batches"
            )
            return True, total_deleted
        except Exception as e:
            logger.error(
                f"Error deleting traces by UUID for project {project_uuid}: {str(e)}"
            )
            return False, 0


def get_opensearch_service() -> OpenSearchService:
    """Get the OpenSearch service instance."""
    return OpenSearchService()
