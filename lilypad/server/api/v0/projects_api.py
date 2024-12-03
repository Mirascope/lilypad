"""The `/projects` API router."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError

from ...models import ProjectCreate, ProjectPublic, ProjectTable
from ...services import ProjectService

projects_router = APIRouter()


@projects_router.get("/projects", response_model=Sequence[ProjectPublic])
async def get_projects(
    project_service: Annotated[ProjectService, Depends(ProjectService)],
) -> Sequence[ProjectTable]:
    """Get all projects."""
    return project_service.find_all_records()


@projects_router.get("/projects/{project_uuid}", response_model=ProjectPublic)
async def get_project(
    project_uuid: UUID,
    project_service: Annotated[ProjectService, Depends(ProjectService)],
) -> ProjectTable:
    """Get a project."""
    return project_service.find_record_by_uuid(project_uuid)


@projects_router.post("/projects/", response_model=ProjectPublic)
async def create_project(
    project_create: ProjectCreate,
    project_service: Annotated[ProjectService, Depends(ProjectService)],
) -> ProjectTable:
    """Create a project"""
    try:
        return project_service.create_record(project_create)
    except IntegrityError:
        raise ValueError("Project already exists")


@projects_router.delete("/projects/{project_uuid}")
async def delete_project(
    project_uuid: UUID,
    project_service: Annotated[ProjectService, Depends(ProjectService)],
) -> None:
    """Create a project"""
    return project_service.delete_record_by_uuid(project_uuid)


__all__ = ["projects_router"]
