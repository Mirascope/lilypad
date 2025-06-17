"""The `/comments` API router."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError

from ..._utils import get_current_user
from ...models.comments import CommentTable
from ...schemas.comments import CommentCreate, CommentPublic, CommentUpdate
from ...schemas.users import UserPublic
from ...services import CommentService

comments_router = APIRouter()


@comments_router.get("/comments", response_model=Sequence[CommentPublic])
async def get_comments(
    comment_service: Annotated[CommentService, Depends(CommentService)],
) -> Sequence[CommentTable]:
    """Get all comments."""
    return comment_service.find_all_records()


@comments_router.get(
    "/spans/{span_uuid}/comments", response_model=Sequence[CommentPublic]
)
async def get_comments_by_spans(
    span_uuid: UUID,
    comment_service: Annotated[CommentService, Depends(CommentService)],
) -> Sequence[CommentTable]:
    """Get all comments by span."""
    return comment_service.find_by_spans(span_uuid)


@comments_router.get("/comments/{comment_uuid}", response_model=CommentPublic)
async def get_comment(
    comment_uuid: UUID,
    comment_service: Annotated[CommentService, Depends(CommentService)],
) -> CommentTable:
    """Get a comment."""
    return comment_service.find_record_by_uuid(comment_uuid)


@comments_router.post("/comments", response_model=CommentPublic)
async def create_comment(
    comment_create: CommentCreate,
    comment_service: Annotated[CommentService, Depends(CommentService)],
    user: Annotated[UserPublic, Depends(get_current_user)],
) -> CommentTable:
    """Create a comment"""
    try:
        return comment_service.create_record(comment_create, user_uuid=user.uuid)
    except IntegrityError:  # pragma: no cover
        raise ValueError("Comment already exists")


@comments_router.patch("/comments/{comment_uuid}", response_model=CommentPublic)
async def patch_comment(
    comment_uuid: UUID,
    comment_update: CommentUpdate,
    comment_service: Annotated[CommentService, Depends(CommentService)],
) -> CommentTable:
    """Update a comment."""
    comment_update.is_edited = True
    return comment_service.update_record_by_uuid(
        comment_uuid, comment_update.model_dump(exclude_unset=True)
    )


@comments_router.delete("/comments/{comment_uuid}")
async def delete_comment(
    comment_uuid: UUID,
    comment_service: Annotated[CommentService, Depends(CommentService)],
) -> bool:
    """Delete a comment"""
    return comment_service.delete_record_by_uuid(comment_uuid)


__all__ = ["comments_router"]
