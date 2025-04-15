"""The EE `/annotations` API router."""

from collections.abc import AsyncGenerator, Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.responses import StreamingResponse

from ee import Tier

from .....server._utils import get_current_user
from .....server.schemas import UserPublic
from .....server.schemas.spans import SpanMoreDetails
from .....server.services import ProjectService, SpanService, UserService
from ....server.schemas import AnnotationCreate, AnnotationPublic, AnnotationUpdate
from ....server.services import AnnotationService
from ...generations.annotate_trace import annotate_trace
from ...require_license import require_license

annotations_router = APIRouter()


@annotations_router.post(
    "/projects/{project_uuid}/annotations",
    response_model=Sequence[AnnotationPublic],
)
@require_license(tier=Tier.ENTERPRISE, cloud_free=True)
async def create_annotations(
    project_uuid: UUID,
    annotations_service: Annotated[AnnotationService, Depends(AnnotationService)],
    project_service: Annotated[ProjectService, Depends(ProjectService)],
    annotations_create: Sequence[AnnotationCreate],
) -> Sequence[AnnotationPublic]:
    """Create an annotation.

    Args:
        project_uuid: The project UUID.
        annotations_service: The annotation service.
        annotations_create: The annotation create model.

    Returns:
        AnnotationPublic: The created annotation.

    Raises:
        HTTPException: If the span has already been assigned to a user and has
        not been labeled yet.
    """
    duplicate_checks = []
    processed_creates: list[AnnotationCreate] = []
    emails_to_lookup: set[str] = set()
    email_to_uuid_map: dict[str, UUID] = {}

    for annotation in annotations_create:
        if annotation.assignee_email:
            emails_to_lookup.add(annotation.assignee_email)
            processed_creates.append(
                annotation.model_copy(update={"assignee_email": None})
            )
        elif annotation.assigned_to:
            for user_uuid in annotation.assigned_to:
                duplicate_checks.append(
                    {"span_uuid": annotation.span_uuid, "assigned_to": user_uuid}
                )
            processed_creates.append(annotation.model_copy())
        else:
            duplicate_checks.append({"span_uuid": annotation.span_uuid})
            processed_creates.append(annotation.model_copy())

    if emails_to_lookup:
        project = project_service.find_record_by_uuid(project_uuid)
        email_to_uuid_lookup = {
            user_organizations.user.email: user_organizations.user.uuid
            for user_organizations in project.organization.user_organizations
        }
        for email in emails_to_lookup:
            if email in email_to_uuid_lookup:
                email_to_uuid_map[email] = email_to_uuid_lookup[email]
            else:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    f"User with email '{email}' not found in accessible organizations.",
                )

    final_creates: list[AnnotationCreate] = []
    for ann_create_processed in processed_creates:
        original_input = next(
            (
                item
                for item in annotations_create
                if item.span_uuid == ann_create_processed.span_uuid
            ),
            None,
        )
        if original_input and original_input.assignee_email:
            assignee_uuid = email_to_uuid_map.get(original_input.assignee_email)
            if assignee_uuid:
                ann_create_processed.assigned_to = [assignee_uuid]
                duplicate_checks.append(
                    {
                        "span_uuid": ann_create_processed.span_uuid,
                        "assigned_to": assignee_uuid,
                    }
                )
        final_creates.append(ann_create_processed)

    # Check for duplicates in bulk
    duplicates = annotations_service.check_bulk_duplicates(duplicate_checks)
    if duplicates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Duplicates found for spans: {', '.join(str(d) for d in duplicates)}",
        )

    # Create all records in bulk
    annotations = annotations_service.create_bulk_records(
        final_creates, project_uuid
    )
    return [
        AnnotationPublic.model_validate(
            annotation, update={"span": SpanMoreDetails.from_span(annotation.span)}
        )
        for annotation in annotations
    ]


@annotations_router.patch(
    "/projects/{project_uuid}/annotations/{annotation_uuid}",
    response_model=AnnotationPublic,
)
@require_license(tier=Tier.ENTERPRISE, cloud_free=True)
async def update_annotation(
    annotation_uuid: UUID,
    annotations_service: Annotated[AnnotationService, Depends(AnnotationService)],
    annotation_update: AnnotationUpdate,
) -> AnnotationPublic:
    """Update an annotation."""
    new_annotation = annotations_service.update_record_by_uuid(
        annotation_uuid, annotation_update.model_dump(exclude_unset=True)
    )
    return AnnotationPublic.model_validate(
        new_annotation, update={"span": SpanMoreDetails.from_span(new_annotation.span)}
    )


@annotations_router.get(
    "/projects/{project_uuid}/functions/{function_uuid}/annotations",
    response_model=Sequence[AnnotationPublic],
)
@require_license(tier=Tier.ENTERPRISE, cloud_free=True)
async def get_annotations_by_functions(
    project_uuid: UUID,
    function_uuid: UUID,
    annotations_service: Annotated[AnnotationService, Depends(AnnotationService)],
) -> Sequence[AnnotationPublic]:
    """Get annotations by functions."""
    return [
        AnnotationPublic.model_validate(
            annotation, update={"span": SpanMoreDetails.from_span(annotation.span)}
        )
        for annotation in annotations_service.find_records_by_function_uuid(
            function_uuid
        )
    ]


@annotations_router.get(
    "/projects/{project_uuid}/annotations",
    response_model=Sequence[AnnotationPublic],
)
@require_license(tier=Tier.ENTERPRISE, cloud_free=True)
async def get_annotations_by_project(
    project_uuid: UUID,
    annotations_service: Annotated[AnnotationService, Depends(AnnotationService)],
) -> Sequence[AnnotationPublic]:
    """Get annotations by project."""
    return [
        AnnotationPublic.model_validate(
            annotation, update={"span": SpanMoreDetails.from_span(annotation.span)}
        )
        for annotation in annotations_service.find_records_by_project_uuid(project_uuid)
    ]


@annotations_router.get(
    "/projects/{project_uuid}/spans/{span_uuid}/generate-annotation"
)
@require_license(tier=Tier.ENTERPRISE, cloud_free=True)
async def generate_annotation(
    span_uuid: UUID,
    annotation_service: Annotated[AnnotationService, Depends(AnnotationService)],
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> StreamingResponse:
    """Stream function."""
    data = {}
    annotation = annotation_service.find_record_by_span_uuid(span_uuid)
    if not annotation:
        span = span_service.find_record_by_uuid(span_uuid)
        if not span:
            raise HTTPException(status_code=404, detail="Span not found")
        else:
            attributes = span.data.get("attributes", {})
            lilypad_type = attributes.get("lilypad.type")
            output = attributes.get(f"lilypad.{lilypad_type}.output", None)
            if isinstance(output, str):
                data["output"] = {
                    "idealOutput": output,
                    "reasoning": "",
                    "exact": False,
                    "label": None,
                }
            elif isinstance(output, dict):
                for key, value in output.items():
                    data[key] = {
                        "idealOutput": value,
                        "reasoning": "",
                        "exact": False,
                        "label": None,
                    }
    else:
        if annotation.data:
            data = annotation.data

    async def stream() -> AsyncGenerator[str, None]:
        r"""Stream the function. Must yield 'data: {your_data}\n\n'."""
        async for chunk in annotate_trace():
            yield f"data: {chunk.model_dump_json()}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
