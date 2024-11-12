"""The `/projects` API router."""

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends

from ...models import ProjectCreate, ProjectPublic, ProjectTable
from ...services import ProjectService

projects_router = APIRouter()


@projects_router.get("/projects", response_model=Sequence[ProjectPublic])
async def get_projects(
    project_service: Annotated[ProjectService, Depends(ProjectService)],
) -> Sequence[ProjectTable]:
    """Get all projects."""
    return project_service.find_all_records()


@projects_router.get("/projects/{project_id}", response_model=ProjectPublic)
async def get_project(
    project_id: int,
    project_service: Annotated[ProjectService, Depends(ProjectService)],
) -> ProjectTable:
    """Get a project."""
    return project_service.find_record_by_id(project_id)


@projects_router.post("/projects/", response_model=ProjectPublic)
async def create_project(
    project_create: ProjectCreate,
    project_service: Annotated[ProjectService, Depends(ProjectService)],
) -> ProjectTable:
    """Create a project"""
    return project_service.create_record(project_create)


@projects_router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    project_service: Annotated[ProjectService, Depends(ProjectService)],
) -> None:
    """Create a project"""
    return project_service.delete_record_by_id(project_id)


__all__ = ["projects_router"]
