from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from ee import Tier
from lilypad.ee.server.require_license import require_license
from lilypad.ee.server.schemas import AnnotationPublic
from lilypad.ee.server.schemas.spans import SpanAssignmentUpdate
from lilypad.ee.server.services import AnnotationService
from lilypad.server._utils import get_current_user
from lilypad.server.schemas import SpanMoreDetails, UserPublic
from lilypad.server.services import SpanService, UserService

spans_router = APIRouter()


@spans_router.patch(
    "/projects/{project_uuid}/spans/{span_uuid}/assignment",
    response_model=list[AnnotationPublic],
    summary="Assign Annotation to User",
    description="Assigns the annotation associated with the given span to a user specified by email. If no annotation exists, it will be created.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Span or User not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid input or state"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)
@require_license(tier=Tier.ENTERPRISE, cloud_free=True)
async def assign_span_annotation(
    span_uuid: UUID,
    assignment_data: SpanAssignmentUpdate,
    span_service: Annotated[SpanService, Depends(SpanService)],
    annotation_service: Annotated[AnnotationService, Depends(AnnotationService)],
    user_service: Annotated[UserService, Depends(UserService)],
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> list[AnnotationPublic]:
    """Handles assigning the annotation for a span_uuid to a user by email."""
    organization_uuids_to_search = [
        user_org.organization_uuid for user_org in current_user.user_organizations or []
    ]
    if not organization_uuids_to_search:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user does not belong to any organizations.",
        )

    assignee = user_service.find_record_by_email_in_organizations(
        email=assignment_data.assignee_email,
        organization_uuids=organization_uuids_to_search,
    )
    if not assignee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{assignment_data.assignee_email}' not found in accessible organizations.",
        )
    assignee_uuid = assignee.uuid

    try:
        span = span_service.find_record_by_uuid(span_uuid)
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Span with UUID '{span_uuid}' not found or not accessible.",
            )
        raise e

    if not span.project_uuid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Span {span_uuid} is missing project association.",
        )

    annotations = annotation_service.find_records_by_span_uuid(span_uuid)

    if annotations:
        try:
            annotation_to_returns = [
                annotation_service.update_record_by_uuid(
                    uuid=annotation.uuid,
                    data={"assigned_to": assignee_uuid},
                    project_uuid=span.project_uuid,
                )
                for annotation in annotations
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update annotation assignment: {e}",
            )
    else:
        try:
            annotation_to_returns = [
                annotation_service.create_record(
                    data=annotation_service.create_model(),
                    span_uuid=span_uuid,
                    project_uuid=span.project_uuid,
                    function_uuid=span.function_uuid,
                    assigned_to=assignee_uuid,
                )
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create annotation for assignment: {e}",
            )

    refreshed_annotations = [
        annotation_service.find_record_by_uuid(
            annotation_to_return.uuid, project_uuid=span.project_uuid
        )
        for annotation_to_return in annotation_to_returns
    ]

    return [
        AnnotationPublic.model_validate(
            refreshed_annotation, update={"span": SpanMoreDetails.from_span(refreshed_annotation.span)}
        )
        for refreshed_annotation in refreshed_annotations
    ]


__all__ = ["spans_router"]
