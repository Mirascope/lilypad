"""The `/functions` API router."""

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends

from ...services import FunctionService

functions_router = APIRouter()


@functions_router.get(
    "/projects/{project_id}/functions/names", response_model=Sequence[str]
)
async def get_unique_function_names(
    project_id: int,
    function_service: Annotated[FunctionService, Depends(FunctionService)],
) -> Sequence[str]:
    """Get all projects."""
    return function_service.find_unique_function_names_by_project_id(project_id)


__all__ = ["functions_router"]
