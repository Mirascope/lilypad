"""OpenSearch utilities for Lilypad server."""

import logging
from uuid import UUID

from ..services import OpenSearchService

logger = logging.getLogger(__name__)


async def index_traces_in_opensearch(
    project_uuid: UUID,
    environment_uuid: UUID,
    traces: list[dict],
    opensearch_service: OpenSearchService,
) -> None:
    """Index traces in OpenSearch."""
    try:
        success = opensearch_service.bulk_index_traces(
            project_uuid, environment_uuid, traces
        )
        if not success:
            logger.error(
                f"Failed to index {len(traces)} traces for project {project_uuid} and environment {environment_uuid}"
            )
        else:
            logger.info(
                f"Successfully indexed {len(traces)} traces for project {project_uuid} and environment {environment_uuid}"
            )
    except Exception as e:
        logger.error(f"Exception during trace indexing: {str(e)}")
