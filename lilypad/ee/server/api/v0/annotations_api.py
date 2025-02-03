"""The EE `/annotations` API router."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException

from ....server.models import (
    AnnotationCreate,
    AnnotationPublic,
    AnnotationTable,
    AnnotationUpdate,
)
from ....server.services import AnnotationService
from ... import validate_license

validate_license()
annotations_router = APIRouter()


@annotations_router.post(
    "/projects/{project_uuid}/annotations",
    response_model=Sequence[AnnotationPublic],
)
async def create_annotations(
    project_uuid: UUID,
    annotations_service: Annotated[AnnotationService, Depends(AnnotationService)],
    annotations_create: Sequence[AnnotationCreate],
) -> Sequence[AnnotationTable]:
    """Create an annotation.

    Args:
        project_uuid: The project UUID.
        annotations_service: The annotation service.
        annotations_create: The annotation create model.

    Returns:
        AnnotationTable: The created annotation.

    Raises:
        HTTPException: If the span has already been assigned to a user and has
        not been labeled yet.
    """
    duplicate_checks = []
    for annotation in annotations_create:
        annotation.project_uuid = project_uuid
        if annotation.span_uuid:
            duplicate_checks.append(
                {
                    "assigned_to": annotation.assigned_to,
                    "span_uuid": annotation.span_uuid,
                }
            )

    # Check for duplicates in bulk
    duplicates = annotations_service.check_bulk_duplicates(duplicate_checks)
    if duplicates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Duplicates found for spans: {', '.join(str(d) for d in duplicates)}",
        )

    # Create all records in bulk
    return annotations_service.create_bulk_records(annotations_create, project_uuid)


@annotations_router.patch(
    "/projects/{project_uuid}/annotations/{annotation_uuid}",
    response_model=AnnotationPublic,
)
async def update_annotation(
    annotation_uuid: UUID,
    annotations_service: Annotated[AnnotationService, Depends(AnnotationService)],
    annotation_update: AnnotationUpdate,
) -> AnnotationTable:
    """Update an annotation."""
    return annotations_service.update_record_by_uuid(
        annotation_uuid, annotation_update.model_dump(exclude_unset=True)
    )


@annotations_router.get(
    "/projects/{project_uuid}/generations/{generation_uuid}/annotations",
    response_model=Sequence[AnnotationPublic],
)
async def get_annotations(
    project_uuid: UUID,
    generation_uuid: UUID,
    annotations_service: Annotated[AnnotationService, Depends(AnnotationService)],
) -> Sequence[AnnotationTable]:
    """Get annotations by generations."""
    return annotations_service.find_records_by_generation_uuid(generation_uuid)
