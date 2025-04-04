"""The `/tags` API router."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError

from ...models import TagTable
from ...schemas import TagCreate, TagPublic
from ...services import TagService

tags_router = APIRouter()


@tags_router.get("/tags", response_model=Sequence[TagPublic])
async def get_tags(
    tag_service: Annotated[TagService, Depends(TagService)],
) -> Sequence[TagTable]:
    """Get all tags."""
    return tag_service.find_all_records()


@tags_router.get("/tags/{tag_uuid}", response_model=TagPublic)
async def get_tag(
    tag_uuid: UUID,
    tag_service: Annotated[TagService, Depends(TagService)],
) -> TagTable:
    """Get a tag."""
    return tag_service.find_record_by_uuid(tag_uuid)


@tags_router.post("/tags", response_model=TagPublic)
async def create_tag(
    tag_create: TagCreate,
    tag_service: Annotated[TagService, Depends(TagService)],
) -> TagTable:
    """Create a tag"""
    try:
        return tag_service.create_record(tag_create)
    except IntegrityError:
        raise ValueError("Tag already exists")


@tags_router.patch("/tags/{tag_uuid}", response_model=TagPublic)
async def patch_tag(
    tag_uuid: UUID,
    tag_create: TagCreate,
    tag_service: Annotated[TagService, Depends(TagService)],
) -> TagTable:
    """Update a tag."""
    return tag_service.update_record_by_uuid(
        tag_uuid, tag_create.model_dump(exclude_unset=True)
    )


@tags_router.delete("/tags/{tag_uuid}")
async def delete_tag(
    tag_uuid: UUID,
    tag_service: Annotated[TagService, Depends(TagService)],
) -> bool:
    """Delete a tag"""
    return tag_service.delete_record_by_uuid(tag_uuid)


__all__ = ["tags_router"]
